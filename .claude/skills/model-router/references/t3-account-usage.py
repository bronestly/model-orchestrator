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

The only field read from a Codex `auth.json` is `tokens.account_id`. No token,
key or email is printed or copied. Selection rules: see t3-code.md.
"""

import argparse
import glob
import json
import os
import sys
from datetime import datetime, timezone

DRIVERS = {"codex": "codex", "claudeAgent": "claude"}
SCOPED_PREFIX = "seven_day_"  # T3 names a model-specific Claude window seven_day_<model>
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
                "_entry": entry,
                "_cache": cache,
            }
        )
    return accounts, settings is not None


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


def applies(window_id, model):
    """A model-specific window counts only for a leg on that model."""
    if not model or not window_id.startswith(SCOPED_PREFIX):
        return True
    scope = window_id[len(SCOPED_PREFIX):]
    return any(part and part in model.lower() for part in scope.split("_"))


def finish(account, reading, now, stale_s, model):
    account.pop("_entry", None)
    account.pop("_cache", None)
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
            else "no usage data: T3 has not probed this account yet (open its provider "
            "status in T3 Code settings, or run one task on it)"
        )
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
    account["worstUsedPercent"] = worst
    account["headroomPercent"] = 100.0 - worst
    return account


def recommend(accounts, prefer, tie_margin, low_headroom):
    """Most room in the worst window; see t3-code.md for the rule in words."""
    usable = [a for a in accounts if a["enabled"] and a["providerStatus"] in (None, "ready")]
    if not usable:
        return {"instanceId": None, "displayName": None, "reason": "no enabled, ready account"}

    def preferred(a):
        return a["instanceId"] in prefer or a["displayName"] in prefer

    known = [a for a in usable if a["headroomPercent"] is not None]
    unknown = [a for a in usable if a["headroomPercent"] is None]
    best = max((a["headroomPercent"] for a in known), default=None)
    if best is None or (best < low_headroom and unknown):
        pool, why = unknown, (
            "no usage data for any account" if best is None
            else "every account with data has under %d%% left; trying one without data" % low_headroom
        )
        pick = sorted(pool, key=lambda a: not preferred(a))[0]
        return {"instanceId": pick["instanceId"], "displayName": pick["displayName"],
                "reason": why + ("; owner default" if preferred(pick) else "")}
    close = [a for a in known if best - a["headroomPercent"] <= tie_margin]
    # Among near-equal accounts: fresh data first, then the owner's default, then most room.
    close.sort(key=lambda a: (a["state"] != "ok", not preferred(a), -a["headroomPercent"]))
    pick = close[0]
    reason = "%.0f%% left in its worst window" % pick["headroomPercent"]
    others = [a for a in known if a is not pick]
    if others:
        reason += " (%s)" % ", ".join("%s %.0f%%" % (a["displayName"], a["headroomPercent"]) for a in others)
    if len(close) > 1:
        reason += "; within %d points, chosen as %s" % (
            tie_margin,
            "the fresher reading" if close[1]["state"] != "ok" and pick["state"] == "ok"
            else "owner default" if preferred(pick) else "the one with most room",
        )
    if pick["state"] == "stale":
        reason += "; figure is %d min old" % pick["ageMinutes"]
    if pick["headroomPercent"] <= 0:
        resets = [w["resetsAt"] for w in pick["windows"] if w["applies"] and w["usedPercent"] >= 100 and w["resetsAt"]]
        reason = "all accounts are at their limit; earliest known reset %s" % (min(resets) if resets else "unknown")
        return {"instanceId": None, "displayName": None, "reason": reason}
    return {"instanceId": pick["instanceId"], "displayName": pick["displayName"], "reason": reason}


def collect(t3_home, now, stale_minutes=30, model=None, prefer=(), tie_margin=5, low_headroom=10):
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
    done = [finish(a, readings.get(a["instanceId"]), now, stale_minutes * 60, model) for a in accounts]
    done.sort(key=lambda a: (a["provider"], a["instanceId"]))
    result = {
        "generatedAt": iso(now),
        "t3SettingsFound": settings_found,
        "staleAfterMinutes": stale_minutes,
        "model": model,
        "accounts": done,
        "recommended": {},
    }
    for provider in sorted(set(DRIVERS.values())):
        group = [a for a in done if a["provider"] == provider]
        if group:
            result["recommended"][provider] = recommend(group, set(prefer), tie_margin, low_headroom)
    return result


def render(result, show_all, now):
    lines = []
    if not result["t3SettingsFound"]:
        lines.append("T3 settings file not found or unreadable; nothing to discover.")
    for a in result["accounts"]:
        if a["state"] == "disabled" and not show_all:
            continue
        head = "%-6s %s (%s)" % (a["provider"], a["displayName"], a["instanceId"])
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
            " (STALE)" if a["state"] == "stale" else "", a["source"]))
    for provider, pick in result["recommended"].items():
        lines.append("-> %s: %s" % (
            provider,
            "%s (%s): %s" % (pick["displayName"], pick["instanceId"], pick["reason"])
            if pick["instanceId"] else "none: " + pick["reason"]))
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--all", action="store_true", help="also list disabled instances")
    parser.add_argument("--model", help="model of the leg; drops usage windows that belong to another model")
    parser.add_argument("--prefer", action="append", default=[], metavar="INSTANCE",
                        help="owner's default account (instance id or display name); breaks ties; repeatable")
    parser.add_argument("--stale-minutes", type=int, default=30)
    parser.add_argument("--tie-margin", type=int, default=5, help="headroom points that count as a tie")
    parser.add_argument("--t3-home", default=os.environ.get("T3CODE_HOME") or "~/.t3")
    parser.add_argument("--now", help=argparse.SUPPRESS)  # fixed clock for tests
    args = parser.parse_args(argv)
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc).timestamp()
    result = collect(os.path.expanduser(args.t3_home.strip()), now, args.stale_minutes, args.model,
                     args.prefer, args.tie_margin)
    if args.json:
        if not args.all:
            result["accounts"] = [a for a in result["accounts"] if a["state"] != "disabled"]
        print(json.dumps(result, indent=2))
    else:
        print(render(result, args.all, now))
    return 0


if __name__ == "__main__":
    sys.exit(main())
