#!/usr/bin/env python3
"""Compare live provider state with the model-router registry. Stdlib only.

Prints one JSON report on stdout. Exit 0 means the report is complete enough to
read, even if individual sources failed: those appear under "errors", and a run
with errors is never a clean no-change result. The script changes nothing unless
--record is passed, which stores today's upstream versions as reviewed.
"""
import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
STATE_FILE = HOME / ".claude/model-router/upstream-reviewed.json"
INSTALLED_SKILL = HOME / ".claude/skills/model-router/SKILL.md"
T3_CACHES = HOME / ".t3/caches"
VERSION = re.compile(r"\d+\.\d+\.\d+")
# A backticked model ID, optionally with |-separated suffix alternatives. Table rows
# escape the pipe as \|.
MODEL_ID = re.compile(
    r"`((?:gpt|claude|grok|gemini)-[A-Za-z0-9.<-]+(?:\\?\|[a-z]+)*)>?`"
)
PROVIDERS = {"codex": "gpt-", "claude": "claude-", "grok": "grok-", "agy": "gemini-"}

errors = []


def run(*cmd, timeout=45):
    try:
        done = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        errors.append(f"{' '.join(cmd)}: {exc}")
        return None
    if done.returncode != 0:
        errors.append(f"{' '.join(cmd)}: exit {done.returncode}: {done.stderr[-200:]}")
        return None
    return done.stdout


def version_of(text):
    match = VERSION.search(text or "")
    return match.group(0) if match else None


def registry_models(repo):
    text = (repo / ".claude/skills/model-router/references/routing-reference.md").read_text()
    models = set()
    for raw in MODEL_ID.findall(text):
        head, *alternatives = raw.replace("<", "").replace("\\", "").split("|")
        if head.endswith(".md"):
            continue
        models.add(head)
        if alternatives:
            stem = head.rsplit("-", 1)[0]
            models.update(f"{stem}-{suffix}" for suffix in alternatives)
    return models


def t3_catalog(name):
    path = T3_CACHES / f"{name}.json"
    try:
        models = json.loads(path.read_text())["models"]
    except (OSError, ValueError, KeyError) as exc:
        errors.append(f"T3 catalog {path}: {exc}")
        return None
    return {model["slug"] for model in models}


def live_models():
    live = {}
    output = run("codex", "debug", "models")
    if output:
        try:
            live["codex"] = {
                model["slug"]
                for model in json.loads(output)["models"]
                if model.get("visibility") == "list"
            }
        except (ValueError, KeyError) as exc:
            errors.append(f"codex debug models: {exc}")
    output = run("grok", "models")
    if output:
        live["grok"] = set(re.findall(r"^\s*[-*]\s+(\S+)", output, re.M))
    output = run("agy", "models")
    if output:
        live["agy"] = {
            line.split("\t", 1)[0] for line in output.splitlines() if "\t" in line
        }
    # Claude Code has no list command; T3's catalog comes from the installed CLI.
    catalog = t3_catalog("claudeAgent")
    if catalog:
        live["claude"] = catalog
    return live


def upstream_versions():
    versions = {}
    versions["codex"] = (run("gh", "api", "repos/openai/codex/releases/latest", "-q", ".tag_name") or "").strip()
    versions["claude"] = (run("npm", "view", "@anthropic-ai/claude-code", "version") or "").strip()
    output = run("grok", "update", "--check", "--json")
    try:
        versions["grok"] = json.loads(output)["latestVersion"] if output else ""
    except (ValueError, KeyError) as exc:
        errors.append(f"grok update --check: {exc}")
        versions["grok"] = ""
    # agy publishes no release feed: it self-updates, so installed is the best anchor.
    versions["agy"] = version_of(run("agy", "--version"))
    versions["t3"] = (run("gh", "api", "repos/pingdotgg/t3code/releases/latest", "-q", ".tag_name") or "").strip()
    return {
        name: (VERSION.search(value).group(0) if value and VERSION.search(value) else None)
        for name, value in versions.items()
    }


def installed_versions():
    installed = {name: version_of(run(name, "--version")) for name in ("codex", "claude", "grok", "agy")}
    installed["t3_server"] = version_of(run("t3", "--version"))
    plist = "/Applications/T3 Code (Beta).app/Contents/Info"
    if Path(plist + ".plist").exists():
        installed["t3_desktop"] = version_of(run("defaults", "read", plist, "CFBundleShortVersionString"))
    return installed


def skill_version(path):
    try:
        return re.search(r'^\s*version:\s*"([^"]+)"', path.read_text(), re.M).group(1)
    except (OSError, AttributeError):
        return None


def ignored(model, patterns):
    return any(fnmatch.fnmatch(model, pattern) for pattern in patterns)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True, help="origin/master checkout to compare")
    parser.add_argument("--record", action="store_true", help="store upstream versions as reviewed")
    args = parser.parse_args()
    repo = args.repo.resolve()
    config = json.loads(Path(__file__).with_name("probe-config.json").read_text())

    upstream = upstream_versions()
    if args.record:
        if not all(upstream.values()):
            sys.exit(f"Refusing to record incomplete versions: {upstream} {errors}")
        STATE_FILE.write_text(
            json.dumps({"reviewed_at": datetime.now(timezone.utc).isoformat(), "versions": upstream}, indent=2) + "\n"
        )
        print(f"Recorded {upstream} in {STATE_FILE}")
        return

    try:
        reviewed = json.loads(STATE_FILE.read_text())["versions"]
    except (OSError, ValueError, KeyError):
        reviewed = {}
    version_changes = {
        name: {"reviewed": reviewed.get(name), "upstream": value}
        for name, value in upstream.items()
        if value and value != reviewed.get(name)
    }

    registry = registry_models(repo)
    live = live_models()
    new_models, missing_models, t3_gaps = {}, {}, {}
    t3_names = {"codex": "codex", "grok": "grok", "agy": "antigravity", "claude": "claudeAgent"}
    for provider, prefix in PROVIDERS.items():
        if provider not in live:
            errors.append(f"no live model list for {provider}")
            continue
        routed = {model for model in registry if model.startswith(prefix)}
        relevant = {
            model
            for model in live[provider]
            if model.startswith(prefix) and not ignored(model, config["ignore_live"])
        }
        new_models[provider] = sorted(relevant - routed)
        missing_models[provider] = sorted(
            model
            for model in routed - live[provider]
            if not ignored(model, config["ignore_registry"])
        )
        catalog = t3_catalog(t3_names[provider])
        if catalog is not None:
            t3_gaps[provider] = sorted(
                model for model in relevant - catalog if not ignored(model, config["known_t3_gaps"])
            )

    source_skill = skill_version(repo / ".claude/skills/model-router/SKILL.md")
    installed_skill = skill_version(INSTALLED_SKILL)
    report = {
        "first_run": not reviewed,
        "version_changes": version_changes,
        "installed": installed_versions(),
        "new_models": {key: value for key, value in new_models.items() if value},
        "missing_models": {key: value for key, value in missing_models.items() if value},
        "t3_catalog_gaps": {key: value for key, value in t3_gaps.items() if value},
        "skill": {"source": source_skill, "installed": installed_skill, "stale": source_skill != installed_skill},
        "errors": errors,
    }
    report["no_change"] = not (
        version_changes
        or report["new_models"]
        or report["missing_models"]
        or report["t3_catalog_gaps"]
        or report["skill"]["stale"]
        or errors
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
