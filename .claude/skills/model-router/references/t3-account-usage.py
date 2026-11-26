#!/usr/bin/env python3
"""Usage left on each T3 Code Codex and Claude account, and which one to delegate to.

Read-only. Accounts come from the T3 settings file; nothing is hard-coded.
Usage comes from two places, and the newer reading wins:

  1. T3's provider status cache, <t3 home>/caches/<instanceId>.json. T3 probes
     every enabled instance itself and stores `usageLimits` there (Codex and
     Claude alike).
  2. Codex only: the rollout logs under <codex home>/sessions, matched to the
     account by `creator_account_id`. An account that is running right now
     has newer figures there than in the cache.

T3 refreshes its cache only while a T3 client window is open, so a reading can
be old or missing. With --probe the script then asks the provider's own CLI
for that account's limits, the same two requests T3 itself sends: Codex
`account/rateLimits/read` on its app server, and the Claude `get_usage`
control request. Neither sends a prompt, so neither spends model usage.

It also reads the running T3 version and warns when it differs from the one
these file formats were checked against (VERIFIED_T3_VERSION).

The only field read from a Codex `auth.json` is `tokens.account_id`. No token,
key or email is printed or copied. Selection rules: see t3-code.md.
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

DRIVERS = {"codex": "codex", "claudeAgent": "claude"}
SCOPED_PREFIX = "seven_day_"  # T3 names a model-specific Claude window seven_day_<model>
# The T3 server version whose settings file, cache files and MCP tools this script
# and t3-code.md were checked against. model-router-update raises it after
# re-checking a new release (its sources.md, "T3 Code compatibility").
VERIFIED_T3_VERSION = "0.1.12"
# Subscription tiers, lowest first, matched against the plan label T3 shows.
# Pooled plans (business, team, enterprise, edu) are left unranked on purpose.
PLAN_TIERS = {
    "codex": ["free", "go", "plus", "pro 100", "pro 200", "pro 500"],
    "claude": ["free", "pro", "max", "ultra"],
}
PROBE_TIMEOUT_S = 30
PROBE_PLANS = {  # CLI plan codes -> the label T3 shows (CodexProvider.ts, ClaudeProvider.ts)
    "codex": {"prolite": "Pro 100", "pro": "Pro 200", "promax": "Pro 500"},
    "claude": {"max5": "Max", "max20": "Ultra"},
}
ROLLOUT_MAX_FILES = 300
ROLLOUT_MAX_AGE_S = 8 * 24 * 3600  # older than the weekly window says nothing


def load_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def parse_time(value):
    """ISO string or epoch seconds -> epoch seconds, or None."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        text = str(value).strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    except ValueError:
        return None


def iso(epoch):
    if epoch is None:
        return None
    return datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def clean_path(value):
    """Settings paths are typed by hand: strip blanks, expand ~."""
    text = value.strip() if isinstance(value, str) else ""
    return os.path.expanduser(text) if text else ""


def plan_of(provider, cache):
    """(label, rank) from the plan label in T3's cache; rank None when not comparable."""
    auth = (cache or {}).get("auth")
    auth = auth if isinstance(auth, dict) else {}
    label = auth.get("label") or auth.get("type")
    if not isinstance(label, str) or not label.strip():
        return None, None
    label = label.replace("Subscription", "").strip()
    words = " %s " % label.lower()
    rank = None
    for index, tier in enumerate(PLAN_TIERS[provider]):
        if " %s " % tier in words:
            rank = index
    return label, rank


def version_tuple(text):
    parts = []
    for piece in str(text).split("-")[0].split("."):
        if not piece.isdigit():
            return None
        parts.append(int(piece))
    return tuple(parts) or None


def compatibility(t3_home, settings_found, accounts):
    """Compare the running T3 with the version this script was checked against."""
    runtime = load_json(os.path.join(t3_home, "userdata", "server-runtime.json"))
    version = runtime.get("serverVersion") if isinstance(runtime, dict) else None
    version = version if isinstance(version, str) and version else None
    mine, theirs = version_tuple(VERIFIED_T3_VERSION), version_tuple(version) if version else None
    status = "unknown" if theirs is None else "verified" if theirs == mine else "newer" if theirs > mine else "older"
    warnings = []
    if status == "unknown":
        warnings.append("T3 version could not be read (is the T3 server running?); "
                        "checked against %s" % VERIFIED_T3_VERSION)
    elif status != "verified":
        warnings.append("T3 %s is %s than %s, the version this rule was checked against: compare the "
                        "delegate_task, orchestrator_capabilities and task_cancel tools with the list in "
                        "t3-code.md before delegating" % (version, status, VERIFIED_T3_VERSION))
    if not settings_found:
        warnings.append("T3 settings file missing or without a readable providerInstances map")
    for a in accounts:
        if a["enabled"] and a["_shape"]:
            warnings.append("%s (%s): %s" % (a["displayName"], a["instanceId"], a["_shape"]))
    return {"t3Version": version, "verifiedT3Version": VERIFIED_T3_VERSION, "status": status, "warnings": warnings}


def cache_shape_problem(cache):
    """Why a cache file cannot be read as usage, or None. Tells a format change from "not probed"."""
    if cache is None:
        return None
    limits = cache.get("usageLimits")
    if limits is None:
        return None
    if not isinstance(limits, dict) or not isinstance(limits.get("windows"), list):
        return "cache file has usageLimits in an unknown format"
    if isinstance(limits.get("unavailable"), dict):
        return None
    bad = [w for w in limits["windows"]
           if not isinstance(w, dict) or "id" not in w or not isinstance(w.get("usedPercent"), (int, float))]
    if bad or parse_time(limits.get("checkedAt")) is None:
        return "cache file has usage windows in an unknown format"
    return None


def is_enabled(entry, cache):
    """T3's rule (ProviderInstanceRegistry): entry.enabled ?? config.enabled ?? true.

    An instance that is not in the settings file at all takes the value T3
    resolved into its cache file.
    """
    if entry is None:
        return bool((cache or {}).get("enabled"))
    for holder in (entry, entry.get("config")):
        if isinstance(holder, dict) and isinstance(holder.get("enabled"), bool):
            return holder["enabled"]
    return True


def codex_home(entry, cache):
    config = (entry or {}).get("config")
    config = config if isinstance(config, dict) else {}
    paths = (cache or {}).get("runtimePaths")
    paths = paths if isinstance(paths, dict) else {}
    managed = config.get("setupMode") == "managed"
    for candidate in (
        config.get("shadowHomePath"),
        paths.get("shadowHomePath") if managed else None,
        config.get("homePath"),
    ):
        home = clean_path(candidate)
        if home:
            return home
    return os.path.expanduser("~/.codex")


def discover(t3_home):
    """Every Codex and Claude instance T3 knows, enabled or not."""
    settings = load_json(os.path.join(t3_home, "userdata", "settings.json"))
    instances = settings.get("providerInstances") if isinstance(settings, dict) else None
    instances = instances if isinstance(instances, dict) else {}
    found = {}
    for instance_id, entry in instances.items():
        if isinstance(entry, dict) and entry.get("driver") in DRIVERS:
            found[instance_id] = entry
    # The built-in instances exist even when the settings file never mentions them.
    for instance_id in DRIVERS:
        if instance_id not in found and os.path.isfile(cache_path(t3_home, instance_id)):
            found[instance_id] = None
    accounts = []
    for instance_id, entry in found.items():
        cache = load_json(cache_path(t3_home, instance_id))
        cache = cache if isinstance(cache, dict) else None
        driver = entry.get("driver") if entry else instance_id
        accounts.append(
            {
                "provider": DRIVERS[driver],
                "driver": driver,
                "instanceId": instance_id,
                "displayName": (entry or {}).get("displayName")
                or (cache or {}).get("displayName")
                or instance_id,
                "enabled": is_enabled(entry, cache),
                "providerStatus": (cache or {}).get("status"),
                "plan": plan_of(DRIVERS[driver], cache)[0],
                "planRank": plan_of(DRIVERS[driver], cache)[1],
                "_shape": cache_shape_problem(cache),
                "_entry": entry,
                "_cache": cache,
            }
        )
    return accounts, isinstance(settings, dict) and isinstance(settings.get("providerInstances"), dict)


def cache_path(t3_home, instance_id):
    return os.path.join(t3_home, "caches", instance_id + ".json")


def window(window_id, label, minutes, used, resets_at):
    if isinstance(used, bool) or not isinstance(used, (int, float)):
        return None
    minutes = minutes if isinstance(minutes, (int, float)) and not isinstance(minutes, bool) else None
    return {
        "id": str(window_id),
        "label": label or window_label(minutes) or str(window_id),
        "windowMinutes": int(minutes) if minutes else None,
        "reportedUsedPercent": float(used),
        "resetsAtEpoch": parse_time(resets_at),
    }


def window_label(minutes):
    """Name a window by its length, never by its position in the payload."""
    if not minutes:
        return None
    if minutes % 1440 == 0 and minutes >= 1440:
        return "%dd" % (minutes // 1440)
    if minutes % 60 == 0:
        return "%dh" % (minutes // 60)
    return "%dm" % minutes


def reading_from_cache(cache):
    limits = (cache or {}).get("usageLimits")
    if not isinstance(limits, dict):
        return None
    unavailable = limits.get("unavailable")
    if isinstance(unavailable, dict):
        return {"unavailable": unavailable.get("message") or unavailable.get("reason") or "unavailable"}
    windows = []
    for raw in limits.get("windows") or []:
        if not isinstance(raw, dict) or raw.get("id") is None:
            continue
        item = window(
            raw["id"],
            window_label(raw.get("windowDurationMins")),
            raw.get("windowDurationMins"),
            raw.get("usedPercent"),
            raw.get("resetsAt"),
        )
        if item:
            if str(raw["id"]).startswith(SCOPED_PREFIX) and raw.get("label"):
                item["label"] = "%s %s" % (item["label"], str(raw["label"]).split("·")[-1].strip())
            windows.append(item)
    checked = parse_time(limits.get("checkedAt"))
    if not windows or checked is None:
        return None
    return {"source": "t3-cache", "checkedAtEpoch": checked, "windows": windows}


def codex_account_id(home):
    auth = load_json(os.path.join(home, "auth.json"))
    tokens = auth.get("tokens") if isinstance(auth, dict) else None
    account_id = tokens.get("account_id") if isinstance(tokens, dict) else None
    return account_id if isinstance(account_id, str) and account_id else None


def rollout_readings(homes, wanted, now):
    """Latest rate limits per Codex account id, from the newest rollout that has any."""
    files = {}
    for home in homes:
        pattern = os.path.join(home, "sessions", "*", "*", "*", "rollout-*.jsonl")
        for path in glob.glob(pattern):
            try:
                real = os.path.realpath(path)  # homes often share one sessions folder
                files[real] = os.path.getmtime(real)
            except OSError:
                continue
    found = {}
    newest = sorted(files, key=files.get, reverse=True)[:ROLLOUT_MAX_FILES]
    for path in newest:
        if len(found) == len(wanted) or now - files[path] > ROLLOUT_MAX_AGE_S:
            break
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                meta = json.loads(fh.readline())
                payload = meta.get("payload") if isinstance(meta, dict) else None
                account_id = payload.get("creator_account_id") if isinstance(payload, dict) else None
                if account_id not in wanted or account_id in found:
                    continue
                last = None
                for line in fh:
                    if '"rate_limits"' not in line:
                        continue
                    try:
                        record = json.loads(line)
                    except ValueError:
                        continue
                    body = record.get("payload") if isinstance(record, dict) else None
                    if not isinstance(body, dict):
                        continue
                    info = body.get("info")
                    limits = body.get("rate_limits") or (info.get("rate_limits") if isinstance(info, dict) else None)
                    # A model-specific snapshot is not the account's main allowance.
                    if isinstance(limits, dict) and limits.get("limit_id") in (None, "codex"):
                        last = (parse_time(record.get("timestamp")), limits)
        except (OSError, ValueError):
            continue
        if not last:
            continue
        windows = []
        for slot in ("primary", "secondary"):
            raw = last[1].get(slot)
            if isinstance(raw, dict):
                item = window(slot, None, raw.get("window_minutes"), raw.get("used_percent"), raw.get("resets_at"))
                if item:
                    windows.append(item)
        if windows:
            found[account_id] = {
                "source": "codex-rollout",
                "checkedAtEpoch": last[0] or files[path],
                "windows": windows,
            }
    return found


def instance_config(entry):
    config = (entry or {}).get("config")
    return config if isinstance(config, dict) else {}


def run_cli(command, env, requests, is_answer):
    """Send JSON lines to a provider CLI; return its JSON lines up to the one `is_answer` accepts.

    Stdin stays open until the answer arrives: the Codex app server drops a
    request that is still in flight when its input closes.
    """
    try:
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, env=env, text=True)
    except OSError as error:
        return None, "could not start %s: %s" % (command[0], error.strerror or error)
    replies = []
    found = threading.Event()

    def read():
        for line in proc.stdout:
            try:
                reply = json.loads(line)
            except ValueError:
                continue
            if isinstance(reply, dict):
                replies.append(reply)
                if is_answer(reply):
                    break
        found.set()  # answered, or the CLI closed its output

    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    try:
        proc.stdin.write("".join(json.dumps(r) + "\n" for r in requests))
        proc.stdin.flush()
    except OSError:
        pass
    found.wait(PROBE_TIMEOUT_S)
    proc.kill()
    proc.wait()
    reader.join(2)
    return list(replies), None


def probe_plan(provider, code):
    if not isinstance(code, str) or not code.strip() or code == "unknown":
        return None
    name = PROBE_PLANS[provider].get(code.lower(), code.replace("_", " ").title())
    return ("ChatGPT " if provider == "codex" else "Claude ") + name


def probe_codex(entry, cache):
    """Ask the Codex app server for the account's limits. No prompt is sent."""
    binary = clean_path(instance_config(entry).get("binaryPath")) or "codex"
    env = dict(os.environ, CODEX_HOME=codex_home(entry, cache))
    replies, error = run_cli([binary, "app-server"], env, [
        {"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "t3-account-usage", "version": "1"}}},
        {"method": "initialized"},
        {"id": 2, "method": "account/rateLimits/read"},
    ], lambda reply: reply.get("id") == 2)
    if error:
        return {"error": error}
    result = next((r.get("result") for r in replies if r.get("id") == 2), None)
    if not isinstance(result, dict):
        return {"error": "Codex did not answer the usage request"}
    by_id = result.get("rateLimitsByLimitId")
    limits = (by_id.get("codex") if isinstance(by_id, dict) else None) or result.get("rateLimits")
    windows = []
    for slot in ("primary", "secondary"):
        raw = limits.get(slot) if isinstance(limits, dict) else None
        if isinstance(raw, dict):
            item = window(slot, None, raw.get("windowDurationMins"), raw.get("usedPercent"), raw.get("resetsAt"))
            if item:
                windows.append(item)
    if not windows:
        return {"error": "Codex usage answer had no usage window"}
    return {"source": "codex-probe", "windows": windows, "plan": probe_plan("codex", limits.get("planType"))}


def probe_claude(entry, cache):
    """Ask Claude Code for the account's limits through a control request. No prompt is sent."""
    config = instance_config(entry)
    binary = clean_path(config.get("binaryPath")) or "claude"
    # The host session's own CLAUDE* variables would point the probe at the host's account.
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE")}
    home = clean_path(config.get("homePath"))
    if home:
        env["CLAUDE_CONFIG_DIR"] = home
    replies, error = run_cli(
        [binary, "-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose"], env, [
            {"type": "control_request", "request_id": "init", "request": {"subtype": "initialize"}},
            {"type": "control_request", "request_id": "usage",
             "request": {"subtype": "get_usage", "skip_behaviors": True}},
        ], lambda reply: (reply.get("response") or {}).get("request_id") == "usage"
        if isinstance(reply.get("response"), dict) else False)
    if error:
        return {"error": error}
    body = None
    for reply in replies:
        response = reply.get("response")
        if isinstance(response, dict) and response.get("request_id") == "usage":
            body = response.get("response")
    limits = body.get("rate_limits") if isinstance(body, dict) else None
    if not isinstance(limits, dict):
        return {"error": "Claude Code did not answer the usage request"}
    windows = []
    for window_id, minutes in (("five_hour", 300), ("seven_day", 10080)):
        raw = limits.get(window_id)
        if isinstance(raw, dict):
            item = window(window_id, None, minutes, raw.get("utilization"), raw.get("resets_at"))
            if item:
                windows.append(item)
    for raw in limits.get("model_scoped") or []:
        if isinstance(raw, dict) and isinstance(raw.get("display_name"), str):
            name = raw["display_name"]
            item = window(SCOPED_PREFIX + re.sub(r"[^a-z0-9]+", "_", name.lower()), "7d " + name, 10080,
                          raw.get("utilization"), raw.get("resets_at"))
            if item:
                windows.append(item)
    if not windows:
        return {"error": "Claude Code usage answer had no usage window"}
    return {"source": "claude-probe", "windows": windows, "plan": probe_plan("claude", body.get("subscription_type"))}


def run_probes(accounts, readings, now, stale_s, probe):
    """Probe enabled accounts whose reading is missing or stale (or all of them)."""
    def needs(a):
        reading = readings.get(a["instanceId"])
        usable = reading and "unavailable" not in reading
        return a["enabled"] and (probe == "all" or not usable or now - reading["checkedAtEpoch"] > stale_s)

    todo = [a for a in accounts if needs(a)]
    if not todo:
        return
    with ThreadPoolExecutor(max_workers=len(todo)) as pool:
        results = list(pool.map(
            lambda a: (probe_codex if a["driver"] == "codex" else probe_claude)(a["_entry"], a["_cache"]), todo))
    for account, result in zip(todo, results):
        if "error" in result:
            account["_probeError"] = result["error"]
            continue
        result["checkedAtEpoch"] = now
        readings[account["instanceId"]] = result
        if result.get("plan"):
            account["plan"] = result["plan"]
            words = " %s " % result["plan"].lower()
            ranks = [i for i, tier in enumerate(PLAN_TIERS[account["provider"]]) if " %s " % tier in words]
            account["planRank"] = ranks[-1] if ranks else None


def applies(window_id, model):
    """A model-specific window counts only for a leg on that model."""
    if not model or not window_id.startswith(SCOPED_PREFIX):
        return True
    scope = window_id[len(SCOPED_PREFIX):]
    return any(part and part in model.lower() for part in scope.split("_"))


def finish(account, reading, now, stale_s, model):
    account.pop("_entry", None)
    account.pop("_cache", None)
    account.pop("_shape", None)
    probe_error = account.pop("_probeError", None)
    account.update({"state": "unknown", "source": None, "checkedAt": None, "ageMinutes": None,
                    "windows": [], "worstUsedPercent": None, "headroomPercent": None, "note": None})
    if not account["enabled"]:
        account["state"] = "disabled"
        account["note"] = "disabled in T3 settings"
        return account
    if not reading or "unavailable" in reading:
        account["note"] = (
            "no usage data: %s" % reading["unavailable"]
            if reading
            else "no usage data: T3 has not probed this account yet (run again with --probe, "
            "or open T3 Code so it refreshes)"
        )
        if probe_error:
            account["note"] += "; direct probe failed: " + probe_error
        return account
    age = max(0.0, now - reading["checkedAtEpoch"])
    worst = None
    for item in reading["windows"]:
        reset = item.pop("resetsAtEpoch")
        item["resetsAt"] = iso(reset)
        item["resetPassed"] = reset is not None and reset <= now
        item["usedPercent"] = 0.0 if item["resetPassed"] else min(100.0, max(0.0, item["reportedUsedPercent"]))
        item["applies"] = applies(item["id"], model)
        if item["applies"]:
            worst = item["usedPercent"] if worst is None else max(worst, item["usedPercent"])
    account.update({
        "source": reading["source"],
        "checkedAt": iso(reading["checkedAtEpoch"]),
        "ageMinutes": int(age // 60),
        "windows": reading["windows"],
    })
    if worst is None:
        account["note"] = "no usage window applies to this leg"
        return account
    account["state"] = "stale" if age > stale_s else "ok"
    if probe_error:
        account["note"] = "direct probe failed: " + probe_error
    account["worstUsedPercent"] = worst
    account["headroomPercent"] = 100.0 - worst
    return account


def recommend(accounts, tie_margin, low_headroom, plan_floor):
    """Which account to delegate to; see t3-code.md for the rule in words."""
    usable = [a for a in accounts if a["enabled"] and a["providerStatus"] in (None, "ready")]
    if not usable:
        return {"instanceId": None, "displayName": None, "reason": "no enabled, ready account"}

    def rank(a):
        return -1 if a["planRank"] is None else a["planRank"]

    def answer(pick, reason):
        return {"instanceId": pick["instanceId"], "displayName": pick["displayName"], "reason": reason}

    def describe(pick, lead):
        reason = lead
        others = [a for a in known if a is not pick]
        if others:
            reason += " (%s)" % ", ".join("%s %.0f%%" % (a["displayName"], a["headroomPercent"]) for a in others)
        if pick["state"] == "stale":
            reason += "; figure is %d min old" % pick["ageMinutes"]
        return reason

    known = [a for a in usable if a["headroomPercent"] is not None]
    unknown = [a for a in usable if a["headroomPercent"] is None]
    best = max((a["headroomPercent"] for a in known), default=None)
    if best is None or (best < low_headroom and unknown):
        why = ("no usage data for any account" if best is None
               else "every account with data has under %d%% left; trying one without data" % low_headroom)
        return answer(sorted(unknown, key=lambda a: -rank(a))[0], why)
    if best <= 0:
        resets = [w["resetsAt"] for a in known for w in a["windows"]
                  if w["applies"] and w["usedPercent"] >= 100 and w["resetsAt"]]
        return {"instanceId": None, "displayName": None,
                "reason": "all accounts are at their limit; earliest known reset %s" % (min(resets) if resets else "unknown")}
    # A bigger plan's percent is worth more, so the highest plan goes first while it has real room.
    top = max(rank(a) for a in known)
    if top > min(rank(a) for a in known):
        roomy = [a for a in known if rank(a) == top and a["headroomPercent"] >= plan_floor]
        if roomy:
            pick = max(roomy, key=lambda a: a["headroomPercent"])
            return answer(pick, describe(pick, "highest plan (%s) with %.0f%% left in its worst window"
                                         % (pick["plan"], pick["headroomPercent"])))
    close = [a for a in known if best - a["headroomPercent"] <= tie_margin]
    # Among near-equal accounts: fresh data first, then the higher plan, then most room.
    close.sort(key=lambda a: (a["state"] != "ok", -rank(a), -a["headroomPercent"]))
    pick = close[0]
    reason = describe(pick, "%.0f%% left in its worst window" % pick["headroomPercent"])
    if len(close) > 1:
        reason += "; within %d points, chosen as %s" % (
            tie_margin,
            "the fresher reading" if close[1]["state"] != "ok" and pick["state"] == "ok"
            else "the higher plan" if rank(pick) > rank(close[1]) else "the one with most room")
    return answer(pick, reason)


def collect(t3_home, now, stale_minutes=30, model=None, tie_margin=5, low_headroom=10, plan_floor=25,
            probe=None, host=None):
    accounts, settings_found = discover(t3_home)
    readings = {a["instanceId"]: reading_from_cache(a["_cache"]) for a in accounts}
    codex = [a for a in accounts if a["driver"] == "codex" and a["enabled"]]
    homes = {a["instanceId"]: codex_home(a["_entry"], a["_cache"]) for a in codex}
    ids = {instance: codex_account_id(home) for instance, home in homes.items()}
    wanted = {account_id for account_id in ids.values() if account_id}
    rollouts = rollout_readings(sorted(set(homes.values())), wanted, now) if wanted else {}
    for instance, account_id in ids.items():
        newer = rollouts.get(account_id)
        current = readings.get(instance)
        if newer and (not current or "unavailable" in current or newer["checkedAtEpoch"] > current["checkedAtEpoch"]):
            readings[instance] = newer
    compat = compatibility(t3_home, settings_found, accounts)
    if probe:
        run_probes(accounts, readings, now, stale_minutes * 60, probe)
    done = [finish(a, readings.get(a["instanceId"]), now, stale_minutes * 60, model) for a in accounts]
    done.sort(key=lambda a: (a["provider"], a["instanceId"]))
    result = {
        "generatedAt": iso(now),
        "t3SettingsFound": settings_found,
        "compatibility": compat,
        "staleAfterMinutes": stale_minutes,
        "model": model,
        "accounts": done,
        "recommended": {},
    }
    for provider in sorted(set(DRIVERS.values())):
        group = [a for a in done if a["provider"] == provider]
        if group:
            result["recommended"][provider] = recommend(group, tie_margin, low_headroom, plan_floor)
    if host:
        result["host"] = host_advice(done, result["recommended"], host, plan_floor)
    return result


def host_advice(accounts, recommended, host, floor):
    """Should a leg leave the host session's own account? Only when it is low and another has room."""
    mine = next((a for a in accounts if a["instanceId"] == host), None)
    if mine is None:
        return {"instanceId": host, "delegateElsewhere": False, "reason": "host instance not found in T3 settings"}
    advice = {"instanceId": host, "displayName": mine["displayName"], "headroomPercent": mine["headroomPercent"],
              "delegateElsewhere": False, "to": None}
    pick = recommended.get(mine["provider"]) or {}
    other = next((a for a in accounts if a["instanceId"] == pick.get("instanceId")), None)
    if mine["headroomPercent"] is None:
        advice["reason"] = "no usage data for the host account; stay on it"
    elif mine["headroomPercent"] >= floor:
        advice["reason"] = "host account has %.0f%% left; stay on it" % mine["headroomPercent"]
    elif other is None or other is mine or other["headroomPercent"] is None or other["headroomPercent"] < floor:
        advice["reason"] = "host account has %.0f%% left and no other account has %d%% or more" % (
            mine["headroomPercent"], floor)
    else:
        advice.update({"delegateElsewhere": True, "to": other["instanceId"],
                       "reason": "host account has %.0f%% left; %s has %.0f%%" % (
                           mine["headroomPercent"], other["displayName"], other["headroomPercent"])})
    return advice


def render(result, show_all, now):
    lines = []
    if not result["t3SettingsFound"]:
        lines.append("T3 settings file not found or unreadable; nothing to discover.")
    for a in result["accounts"]:
        if a["state"] == "disabled" and not show_all:
            continue
        head = "%-6s %s (%s%s)" % (a["provider"], a["displayName"], a["instanceId"],
                                  ", " + a["plan"] if a["plan"] else "")
        if a["state"] in ("disabled", "unknown"):
            lines.append("%s: %s%s" % (head, "unknown, " if a["state"] == "unknown" else "", a["note"]))
            continue
        parts = []
        for w in a["windows"]:
            text = "%s %.0f%% used" % (w["label"], w["usedPercent"])
            reset = parse_time(w["resetsAt"])
            if w["resetPassed"]:
                text += " (reset passed)"
            elif reset is not None:
                left = int(reset - now) // 60
                text += ", resets in %dh%02dm" % (left // 60, left % 60)
            if not w["applies"]:
                text += " [not this model]"
            parts.append(text)
        lines.append("%s: %s | %.0f%% left | %d min old%s, %s" % (
            head, " | ".join(parts), a["headroomPercent"], a["ageMinutes"],
            " (STALE)" if a["state"] == "stale" else "", a["source"]) + ("; " + a["note"] if a["note"] else ""))
    for provider, pick in result["recommended"].items():
        lines.append("-> %s: %s" % (
            provider,
            "%s (%s): %s" % (pick["displayName"], pick["instanceId"], pick["reason"])
            if pick["instanceId"] else "none: " + pick["reason"]))
    if result.get("host"):
        lines.append("host %s: %s%s" % (result["host"].get("displayName") or result["host"]["instanceId"],
                                        "delegate elsewhere, " if result["host"]["delegateElsewhere"] else "",
                                        result["host"]["reason"]))
    for warning in result["compatibility"]["warnings"]:
        lines.append("WARNING: " + warning)
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--all", action="store_true", help="also list disabled instances")
    parser.add_argument("--model", help="model of the leg; drops usage windows that belong to another model")
    parser.add_argument("--probe", nargs="?", const="needed", choices=["needed", "all"],
                        help="ask the provider CLI directly for accounts with no or stale data "
                             "(--probe=all: every account); sends no prompt")
    parser.add_argument("--host", metavar="INSTANCE",
                        help="instance id of this session's own account; adds advice on whether a leg "
                             "that would run on it should go to another account instead")
    parser.add_argument("--stale-minutes", type=int, default=30)
    parser.add_argument("--tie-margin", type=int, default=5, help="headroom points that count as a tie")
    parser.add_argument("--plan-floor", type=int, default=25,
                        help="the highest-plan account is chosen while it has at least this much left")
    parser.add_argument("--t3-home", default=os.environ.get("T3CODE_HOME") or "~/.t3")
    parser.add_argument("--now", help=argparse.SUPPRESS)  # fixed clock for tests
    args = parser.parse_args(argv)
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc).timestamp()
    result = collect(os.path.expanduser(args.t3_home.strip()), now, args.stale_minutes, args.model,
                     args.tie_margin, plan_floor=args.plan_floor, probe=args.probe, host=args.host)
    if args.json:
        if not args.all:
            result["accounts"] = [a for a in result["accounts"] if a["state"] != "disabled"]
        print(json.dumps(result, indent=2))
    else:
        print(render(result, args.all, now))
    return 0


if __name__ == "__main__":
    sys.exit(main())
