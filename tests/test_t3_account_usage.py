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

    def instance(self, instance_id, driver, name, windows=None, checked=-2, **entry):
        self.instances[instance_id] = {"driver": driver, "displayName": name, **entry}
        if windows is not None:
            self.write(self.t3 / "caches" / (instance_id + ".json"), {
                "enabled": True, "status": "ready",
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

    def test_tie_goes_to_owner_default_and_stale_loses_a_tie(self):
        self.instance("claudeAgent", "claudeAgent", "A", [self.win("seven_day", 40, 10080, 900)])
        self.instance("claudeAgent_b", "claudeAgent", "B", [self.win("seven_day", 43, 10080, 900)])
        result, _ = self.collect()
        self.assertEqual(result["recommended"]["claude"]["instanceId"], "claudeAgent")
        result, _ = self.collect(prefer=["B"])
        self.assertEqual(result["recommended"]["claude"]["instanceId"], "claudeAgent_b")
        self.assertIn("owner default", result["recommended"]["claude"]["reason"])
        # A stale reading still ranks, but a fresh account within the margin wins even over the default.
        self.instance("claudeAgent_b", "claudeAgent", "B", [self.win("seven_day", 38, 10080, 900)], checked=-90)
        result, by_id = self.collect(prefer=["B"])
        self.assertEqual(by_id["claudeAgent_b"]["state"], "stale")
        self.assertEqual(result["recommended"]["claude"]["instanceId"], "claudeAgent")
        # Outside the margin the stale account still wins, and the reason says how old it is.
        self.instance("claudeAgent_b", "claudeAgent", "B", [self.win("seven_day", 5, 10080, 900)], checked=-90)
        result, _ = self.collect()
        self.assertEqual(result["recommended"]["claude"]["instanceId"], "claudeAgent_b")
        self.assertIn("90 min old", result["recommended"]["claude"]["reason"])

    def test_model_specific_window_only_counts_for_that_model(self):
        self.instance("claudeAgent", "claudeAgent", "A", [
            self.win("seven_day", 20, 10080, 900), self.win("seven_day_fable", 90, 10080, 900)])
        _, by_id = self.collect(model="claude-sonnet-5-5")
        self.assertEqual(by_id["claudeAgent"]["headroomPercent"], 80)
        _, by_id = self.collect(model="claude-fable-5-2")
        self.assertEqual(by_id["claudeAgent"]["headroomPercent"], 10)
        _, by_id = self.collect()
        self.assertEqual(by_id["claudeAgent"]["headroomPercent"], 10)

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

    def run_cli(self, *args):
        self.write(self.t3 / "userdata" / "settings.json", {"providerInstances": self.instances})
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
