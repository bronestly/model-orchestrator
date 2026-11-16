#!/usr/bin/env python3
"""Fixture checks for references/t3-account-usage.py. Run: python3 tests/test_t3_account_usage.py"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True  # keep __pycache__ out of references/, which is installed
SCRIPT = Path(__file__).resolve().parents[1] / ".claude/skills/model-router/references/t3-account-usage.py"
spec = importlib.util.spec_from_file_location("t3_account_usage", SCRIPT)
usage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(usage)

NOW = usage.parse_time("2026-11-16T20:00:00Z")
SECRET = "sk-fixture-secret-must-never-appear"


def at(minutes):
    """ISO time `minutes` from NOW."""
    return usage.iso(NOW + minutes * 60)


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.t3 = self.home / ".t3"
        self.instances = {}
        self.t3_version = usage.VERIFIED_T3_VERSION
        self.old_home = os.environ.get("HOME")
        os.environ["HOME"] = str(self.home)

    def tearDown(self):
        if self.old_home is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = self.old_home
        self.tmp.cleanup()

    def write(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")

    def instance(self, instance_id, driver, name, windows=None, checked=-2, plan=None, **entry):
        self.instances[instance_id] = {"driver": driver, "displayName": name, **entry}
        if windows is not None:
            self.write(self.t3 / "caches" / (instance_id + ".json"), {
                "enabled": True, "status": "ready", "auth": {"label": plan} if plan else {},
                "usageLimits": {"checkedAt": at(checked), "windows": windows},
            })

    def codex_account(self, home, account_id):
        self.write(home / "auth.json", {"OPENAI_API_KEY": SECRET,
                                        "tokens": {"access_token": SECRET, "account_id": account_id}})

    def rollout(self, home, account_id, limits, minutes=-1, name="rollout-a.jsonl"):
        lines = [
            {"timestamp": at(minutes - 5), "type": "session_meta", "payload": {"creator_account_id": account_id}},
            {"timestamp": at(minutes), "type": "event_msg",
             "payload": {"type": "token_count", "rate_limits": {"limit_id": "codex", **limits}}},
        ]
        path = home / "sessions" / "2026" / "11" / "16" / name
        self.write(path, "\n".join(json.dumps(line) for line in lines) + "\n")
        stamp = NOW + minutes * 60
        os.utime(path, (stamp, stamp))

    def collect(self, **kwargs):
        self.write(self.t3 / "userdata" / "settings.json", {"providerInstances": self.instances})
        if self.t3_version:
            self.write(self.t3 / "userdata" / "server-runtime.json", {"serverVersion": self.t3_version})
        result = usage.collect(str(self.t3), NOW, **kwargs)
        return result, {a["instanceId"]: a for a in result["accounts"]}

    @staticmethod
    def win(window_id, used, minutes, resets=None):
        item = {"id": window_id, "kind": "other", "label": window_id, "usedPercent": used,
                "windowDurationMins": minutes}
        if resets is not None:
            item["resetsAt"] = at(resets)
        return item


class UsageTests(Fixture):
    def test_one_window_account_is_labelled_by_length(self):
        # A weekly-only account reports its 7-day window in the `primary` slot.
        self.instance("codex", "codex", "A", [self.win("primary", 13, 10080, 600)])
        self.instance("codex_b", "codex", "B", config={"shadowHomePath": "~/.codex_b"})
        self.codex_account(self.home / ".codex_b", "acct-b")
        self.rollout(self.home / ".codex_b", "acct-b",
                     {"primary": {"used_percent": 40.0, "window_minutes": 10080,
                                  "resets_at": NOW + 3600}, "secondary": None})
        _, by_id = self.collect()
        self.assertEqual([w["label"] for w in by_id["codex"]["windows"]], ["7d"])
        self.assertEqual(by_id["codex"]["headroomPercent"], 87)
        self.assertEqual([w["label"] for w in by_id["codex_b"]["windows"]], ["7d"])
        self.assertEqual(by_id["codex_b"]["source"], "codex-rollout")
        self.assertEqual(by_id["codex_b"]["headroomPercent"], 60)

    def test_passed_reset_counts_as_zero(self):
        self.instance("claudeAgent", "claudeAgent", "A",
                      [self.win("five_hour", 96, 300, -10), self.win("seven_day", 30, 10080, 900)])
        _, by_id = self.collect()
        five = by_id["claudeAgent"]["windows"][0]
        self.assertTrue(five["resetPassed"])
        self.assertEqual((five["usedPercent"], five["reportedUsedPercent"]), (0, 96))
        self.assertEqual(by_id["claudeAgent"]["headroomPercent"], 70)

    def test_missing_home_and_missing_data_are_unknown_not_empty(self):
        self.instance("codex_gone", "codex", "Gone", config={"shadowHomePath": "~/does-not-exist"})
        self.instance("claudeAgent_new", "claudeAgent", "New", config={"homePath": "~/nope"})
        self.instance("codex", "codex", "Full", [self.win("primary", 97, 300, 60)])
        result, by_id = self.collect()
        for key in ("codex_gone", "claudeAgent_new"):
            self.assertEqual(by_id[key]["state"], "unknown")
            self.assertIsNone(by_id[key]["headroomPercent"])
            self.assertIn("no usage data", by_id[key]["note"])
        # Unknown is not "empty": it is tried only because the known account is nearly out.
        self.assertEqual(result["recommended"]["codex"]["instanceId"], "codex_gone")
        self.assertIn("without data", result["recommended"]["codex"]["reason"])

    def test_unknown_does_not_beat_an_account_with_room(self):
        self.instance("codex_gone", "codex", "Gone", config={"shadowHomePath": "~/does-not-exist"})
        self.instance("codex", "codex", "Half", [self.win("primary", 50, 300, 60)])
        result, _ = self.collect()
        self.assertEqual(result["recommended"]["codex"]["instanceId"], "codex")

    def test_disabled_instance_is_never_chosen(self):
        self.instance("codex_off", "codex", "Off", [self.win("primary", 1, 300, 60)],
                      enabled=False, config={"setupMode": "managed"})
        self.instance("codex", "codex", "On", [self.win("primary", 80, 300, 60)])
        result, by_id = self.collect()
        self.assertEqual(by_id["codex_off"]["state"], "disabled")
        self.assertEqual(result["recommended"]["codex"]["instanceId"], "codex")
        self.assertNotIn("Off", self.run_cli())
        self.assertIn("disabled in T3 settings", self.run_cli("--all"))

    def test_absent_enabled_key_means_enabled(self):
        self.instance("codex", "codex", "Builtin", [self.win("primary", 5, 300, 60)])
        self.instance("claudeAgent", "claudeAgent", "Null", [self.win("five_hour", 5, 300, 60)], enabled=None)
        _, by_id = self.collect()
        self.assertTrue(by_id["codex"]["enabled"] and by_id["claudeAgent"]["enabled"])

    def test_leading_space_in_home_path(self):
        self.instance("codex_b", "codex", "B", config={"setupMode": "existing", "shadowHomePath": " ~/.codex_b "})
        self.codex_account(self.home / ".codex_b", "acct-b")
        self.rollout(self.home / ".codex_b", "acct-b",
                     {"primary": {"used_percent": 22.0, "window_minutes": 300, "resets_at": NOW + 600},
                      "secondary": {"used_percent": 9.0, "window_minutes": 10080, "resets_at": NOW + 9000}})
        _, by_id = self.collect()
        self.assertEqual(by_id["codex_b"]["state"], "ok")
        self.assertEqual([w["label"] for w in by_id["codex_b"]["windows"]], ["5h", "7d"])
        self.assertEqual(by_id["codex_b"]["headroomPercent"], 78)

    def test_newer_rollout_beats_cache_and_shared_sessions_match_by_account(self):
        # Two homes share one sessions folder through a symlink, as on a real device.
        self.instance("codex", "codex", "A", [self.win("primary", 10, 300, 200)], checked=-20)
        self.instance("codex_b", "codex", "B", [self.win("primary", 30, 300, 200)], checked=-1,
                      config={"shadowHomePath": "~/.codex_b"})
        self.codex_account(self.home / ".codex", "acct-a")
        self.codex_account(self.home / ".codex_b", "acct-b")
        self.rollout(self.home / ".codex", "acct-a",
                     {"primary": {"used_percent": 61.0, "window_minutes": 300, "resets_at": NOW + 600}}, -3, "rollout-a.jsonl")
        self.rollout(self.home / ".codex", "acct-b",
                     {"primary": {"used_percent": 99.0, "window_minutes": 300, "resets_at": NOW + 600}}, -9, "rollout-b.jsonl")
        os.symlink(self.home / ".codex" / "sessions", self.home / ".codex_b" / "sessions")
        _, by_id = self.collect()
        self.assertEqual((by_id["codex"]["source"], by_id["codex"]["worstUsedPercent"]), ("codex-rollout", 61))
        self.assertEqual((by_id["codex_b"]["source"], by_id["codex_b"]["worstUsedPercent"]), ("t3-cache", 30))

    def test_tie_goes_to_fresh_reading_and_stale_still_ranks(self):
        self.instance("claudeAgent", "claudeAgent", "A", [self.win("seven_day", 40, 10080, 900)])
        self.instance("claudeAgent_b", "claudeAgent", "B", [self.win("seven_day", 38, 10080, 900)], checked=-90)
        result, by_id = self.collect()
        self.assertEqual(by_id["claudeAgent_b"]["state"], "stale")
        self.assertEqual(result["recommended"]["claude"]["instanceId"], "claudeAgent")
        self.assertIn("fresher", result["recommended"]["claude"]["reason"])
        # Outside the margin the stale account still wins, and the reason says how old it is.
        self.instance("claudeAgent_b", "claudeAgent", "B", [self.win("seven_day", 5, 10080, 900)], checked=-90)
        result, _ = self.collect()
        self.assertEqual(result["recommended"]["claude"]["instanceId"], "claudeAgent_b")
        self.assertIn("90 min old", result["recommended"]["claude"]["reason"])

    def test_higher_plan_goes_first_while_it_has_room(self):
        plus, pro = "ChatGPT Plus Subscription", "ChatGPT Pro 100 Subscription"
        self.instance("codex", "codex", "Small", [self.win("primary", 10, 300, 60)], plan=plus)
        self.instance("codex_b", "codex", "Big", [self.win("primary", 60, 10080, 600)], plan=pro)
        result, by_id = self.collect()
        self.assertEqual((by_id["codex"]["planRank"], by_id["codex_b"]["planRank"]), (2, 3))
        self.assertEqual(result["recommended"]["codex"]["instanceId"], "codex_b")
        self.assertIn("highest plan (ChatGPT Pro 100)", result["recommended"]["codex"]["reason"])
        # Under the floor the bigger plan no longer goes first: most room wins.
        self.instance("codex_b", "codex", "Big", [self.win("primary", 80, 10080, 600)], plan=pro)
        result, _ = self.collect()
        self.assertEqual(result["recommended"]["codex"]["instanceId"], "codex")
        # Equal or unranked plans fall back to most room.
        self.instance("codex_b", "codex", "Big", [self.win("primary", 60, 10080, 600)], plan="ChatGPT Business Subscription")
        result, by_id = self.collect()
        self.assertIsNone(by_id["codex_b"]["planRank"])
        self.assertEqual(result["recommended"]["codex"]["instanceId"], "codex")

    def test_version_and_format_warnings(self):
        self.instance("codex", "codex", "A", [self.win("primary", 10, 300, 60)])
        result, _ = self.collect()
        self.assertEqual((result["compatibility"]["status"], result["compatibility"]["warnings"]), ("verified", []))
        self.t3_version = "9.0.0"
        result, _ = self.collect()
        self.assertEqual(result["compatibility"]["status"], "newer")
        self.assertIn("delegate_task", result["compatibility"]["warnings"][0])
        self.assertIn("WARNING: T3 9.0.0 is newer", self.run_cli())
        self.t3_version = "0.1.2"
        self.assertEqual(self.collect()[0]["compatibility"]["status"], "older")
        # A renamed field in the cache is reported as a format change, and the account is unknown.
        self.t3_version = usage.VERIFIED_T3_VERSION
        self.write(self.t3 / "caches" / "codex.json", {"enabled": True, "status": "ready", "usageLimits": {
            "checkedAt": at(-1), "windows": [{"id": "primary", "percentUsed": 10}]}})
        result, by_id = self.collect()
        self.assertEqual(by_id["codex"]["state"], "unknown")
        self.assertIn("unknown format", result["compatibility"]["warnings"][0])
        os.remove(self.t3 / "userdata" / "server-runtime.json")
        self.t3_version = None
        self.assertEqual(self.collect()[0]["compatibility"]["status"], "unknown")

    def test_model_specific_window_only_counts_for_that_model(self):
        self.instance("claudeAgent", "claudeAgent", "A", [
            self.win("seven_day", 20, 10080, 900), self.win("seven_day_fable", 90, 10080, 900)])
        _, by_id = self.collect(model="claude-sonnet-5-5")
        self.assertEqual(by_id["claudeAgent"]["headroomPercent"], 80)
        _, by_id = self.collect(model="claude-fable-5-2")
        self.assertEqual(by_id["claudeAgent"]["headroomPercent"], 10)
        _, by_id = self.collect()
        self.assertEqual(by_id["claudeAgent"]["headroomPercent"], 10)

    def test_host_advice_switches_only_when_host_is_low_and_another_has_room(self):
        self.instance("claudeAgent", "claudeAgent", "Host", [self.win("seven_day", 90, 10080, 900)])
        self.instance("claudeAgent_b", "claudeAgent", "Other", [self.win("seven_day", 30, 10080, 900)])
        result, _ = self.collect(host="claudeAgent")
        self.assertEqual((result["host"]["delegateElsewhere"], result["host"]["to"]), (True, "claudeAgent_b"))
        # The other account is low as well: stay.
        self.instance("claudeAgent_b", "claudeAgent", "Other", [self.win("seven_day", 85, 10080, 900)])
        self.assertFalse(self.collect(host="claudeAgent")[0]["host"]["delegateElsewhere"])
        # The host has room: stay, even though the other account has more.
        self.instance("claudeAgent", "claudeAgent", "Host", [self.win("seven_day", 60, 10080, 900)])
        self.instance("claudeAgent_b", "claudeAgent", "Other", [self.win("seven_day", 5, 10080, 900)])
        self.assertFalse(self.collect(host="claudeAgent")[0]["host"]["delegateElsewhere"])
        # A model-specific window can make the host low for one model only.
        self.instance("claudeAgent", "claudeAgent", "Host", [
            self.win("seven_day", 20, 10080, 900), self.win("seven_day_fable", 95, 10080, 900)])
        self.assertTrue(self.collect(host="claudeAgent", model="claude-fable-5-2")[0]["host"]["delegateElsewhere"])
        self.assertFalse(self.collect(host="claudeAgent", model="claude-sonnet-5-5")[0]["host"]["delegateElsewhere"])
        self.assertFalse(self.collect(host="nope")[0]["host"]["delegateElsewhere"])

    def test_all_accounts_at_limit_names_the_reset(self):
        self.instance("codex", "codex", "A", [self.win("primary", 100, 300, 45)])
        result, _ = self.collect()
        self.assertIsNone(result["recommended"]["codex"]["instanceId"])
        self.assertIn(at(45), result["recommended"]["codex"]["reason"])

    def test_no_t3_home_and_broken_files_do_not_fail(self):
        result = usage.collect(str(self.home / "missing"), NOW)
        self.assertEqual((result["accounts"], result["t3SettingsFound"]), ([], False))
        self.instance("codex", "codex", "A")
        self.write(self.t3 / "caches" / "codex.json", "{not json")
        self.write(self.home / ".codex" / "auth.json", "[]")
        self.write(self.home / ".codex" / "sessions" / "2026" / "11" / "16" / "rollout-x.jsonl", "garbage\n")
        _, by_id = self.collect()
        self.assertEqual(by_id["codex"]["state"], "unknown")

    def fake_cli(self, name, body):
        """A stand-in provider CLI on PATH that logs its home and prints canned replies."""
        bin_dir = self.home / "bin"
        self.write(bin_dir / name, "#!%s\nimport json, os, sys\nsys.stdin.readline()\n"
                   "open(os.path.join(%r, %r), 'a').write((os.environ.get('CODEX_HOME') or "
                   "os.environ.get('CLAUDE_CONFIG_DIR') or 'default') + '\\n')\n%s\n"
                   % (sys.executable, str(self.home), name + ".calls", body))
        os.chmod(bin_dir / name, 0o755)
        self.addCleanup(os.environ.__setitem__, "PATH", os.environ["PATH"])
        if str(bin_dir) not in os.environ["PATH"]:
            os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ["PATH"]

    def calls(self, name):
        path = self.home / (name + ".calls")
        return path.read_text().split() if path.exists() else []

    def test_probe_fills_missing_and_stale_accounts_only(self):
        self.fake_cli("codex", "print(json.dumps({'id': 2, 'result': {'rateLimits': {'planType': 'prolite', "
                      "'primary': {'usedPercent': 21, 'windowDurationMins': 10080, 'resetsAt': %d}, "
                      "'secondary': None}}}), flush=True)\nsys.stdin.read()" % (NOW + 3600))
        self.fake_cli("claude", "print(json.dumps({'type': 'control_response', 'response': {'request_id': 'usage', "
                      "'response': {'subscription_type': 'max', 'rate_limits': {"
                      "'five_hour': {'utilization': 9, 'resets_at': None}, "
                      "'seven_day': {'utilization': 30, 'resets_at': '%s'}, "
                      "'model_scoped': [{'display_name': 'Fable', 'utilization': 44, 'resets_at': None}]}}}}))" % at(600))
        self.instance("codex", "codex", "Fresh", [self.win("primary", 50, 300, 60)])
        self.instance("codex_b", "codex", "Missing", config={"shadowHomePath": " ~/.codex_b"})
        self.instance("claudeAgent", "claudeAgent", "Stale", [self.win("seven_day", 80, 10080, 900)], checked=-300)
        self.instance("claudeAgent_b", "claudeAgent", "Other", config={"homePath": "~/.claude_b"})
        self.instance("codex_off", "codex", "Off", enabled=False)
        result, by_id = self.collect(probe="needed")
        self.assertEqual(by_id["codex"]["source"], "t3-cache")  # fresh: left alone
        self.assertEqual((by_id["codex_b"]["source"], by_id["codex_b"]["headroomPercent"]), ("codex-probe", 79))
        self.assertEqual((by_id["codex_b"]["plan"], by_id["codex_b"]["planRank"]), ("ChatGPT Pro 100", 3))
        self.assertEqual([w["label"] for w in by_id["codex_b"]["windows"]], ["7d"])
        self.assertEqual((by_id["claudeAgent"]["source"], by_id["claudeAgent"]["state"]), ("claude-probe", "ok"))
        self.assertEqual([w["id"] for w in by_id["claudeAgent"]["windows"]], ["five_hour", "seven_day", "seven_day_fable"])
        self.assertEqual(by_id["claudeAgent"]["headroomPercent"], 56)
        self.assertEqual(self.calls("codex"), [str(self.home / ".codex_b")])
        self.assertEqual(sorted(self.calls("claude")), sorted(["default", str(self.home / ".claude_b")]))
        self.assertEqual(by_id["codex_off"]["state"], "disabled")
        # Without --probe nothing is started.
        (self.home / "codex.calls").unlink()
        self.collect()
        self.assertEqual(self.calls("codex"), [])
        self.collect(probe="all")
        self.assertEqual(len(self.calls("codex")), 2)

    def test_failed_probe_leaves_the_account_unknown_with_the_reason(self):
        self.fake_cli("codex", "print('not json', flush=True)")
        self.instance("codex", "codex", "A")
        self.instance("claudeAgent", "claudeAgent", "B", config={"binaryPath": "~/no-such-claude"})
        _, by_id = self.collect(probe="needed")
        self.assertEqual(by_id["codex"]["state"], "unknown")
        self.assertIn("did not answer", by_id["codex"]["note"])
        self.assertEqual(by_id["claudeAgent"]["state"], "unknown")
        self.assertIn("could not start", by_id["claudeAgent"]["note"])

    def run_cli(self, *args):
        self.write(self.t3 / "userdata" / "settings.json", {"providerInstances": self.instances})
        if self.t3_version:
            self.write(self.t3 / "userdata" / "server-runtime.json", {"serverVersion": self.t3_version})
        out = subprocess.run([sys.executable, str(SCRIPT), "--t3-home", str(self.t3), "--now", at(0), *args],
                             capture_output=True, text=True, check=True)
        return out.stdout + out.stderr

    def test_cli_output_is_valid_json_and_carries_no_secret(self):
        self.instance("codex", "codex", "A", [self.win("primary", 10, 300, 60)])
        self.codex_account(self.home / ".codex", "acct-a")
        self.rollout(self.home / ".codex", "acct-a",
                     {"primary": {"used_percent": 12.0, "window_minutes": 300, "resets_at": NOW + 600}})
        text = self.run_cli("--json")
        self.assertEqual(json.loads(text)["recommended"]["codex"]["instanceId"], "codex")
        for output in (text, self.run_cli(), self.run_cli("--all")):
            self.assertNotIn(SECRET, output)
            self.assertNotIn("acct-a", output)


if __name__ == "__main__":
    unittest.main()
