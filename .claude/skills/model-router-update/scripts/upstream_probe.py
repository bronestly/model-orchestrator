#!/usr/bin/env python3
"""Compare live provider state with the model-router registry. Stdlib only.

With --repo, prints one JSON report on stdout and changes nothing. Sources that fail
appear under "errors", and a report with errors is never a clean no-change result.
With --record, stores the versions from a saved report as reviewed, so a release that
ships during a run stays pending for the next one.
"""
import argparse
import fnmatch
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
ROUTER_STATE = HOME / ".claude/model-router"
STATE_FILE = ROUTER_STATE / "upstream-reviewed.json"
INSTALLED_COMMIT = ROUTER_STATE / "installed-commit"
T3_CACHES = HOME / ".t3/caches"
VERSION = re.compile(r"\d+\.\d+\.\d+")
# A backticked model ID, optionally with |-separated suffix alternatives. Table rows
# escape the pipe as \|.
MODEL_ID = re.compile(
    r"`((?:gpt|claude|grok|gemini)-[A-Za-z0-9.<-]+(?:\\?\|[a-z]+)*)>?`"
)
# provider: (prefix of its registry IDs, whether its live list carries other vendors)
PROVIDERS = {
    "codex": ("gpt-", False),
    "claude": ("claude-", False),
    "grok": ("grok-", True),
    "agy": ("gemini-", True),
}
T3_CATALOGS = {"codex": "codex", "grok": "grok", "agy": "antigravity", "claude": "claudeAgent"}

errors = []
notices = []


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


def t3_cache(name):
    path = T3_CACHES / f"{name}.json"
    try:
        cache = json.loads(path.read_text())
        return {"version": cache.get("version"), "slugs": {model["slug"] for model in cache["models"]}}
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        errors.append(f"T3 catalog {path}: {exc!r}")
        return None


def parsed(label, parse, output):
    """Run a parser over a CLI's output; a shape it did not expect is a failed source."""
    if not output:
        return None
    try:
        return parse(output)
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        errors.append(f"{label}: {exc!r}")
        return None


def live_models():
    live = {
        "codex": parsed(
            "codex debug models",
            lambda text: {
                model["slug"]
                for model in json.loads(text)["models"]
                if model.get("visibility") == "list"
            },
            run("codex", "debug", "models"),
        ),
        "grok": parsed(
            "grok models",
            lambda text: set(re.findall(r"^\s*[-*]\s+(\S+)", text, re.M)),
            run("grok", "models"),
        ),
        "agy": parsed(
            "agy models",
            lambda text: {line.split("\t", 1)[0] for line in text.splitlines() if "\t" in line},
            run("agy", "models"),
        ),
    }
    # Claude Code has no list command; T3's catalog comes from the installed CLI.
    catalog = t3_cache("claudeAgent")
    if catalog:
        live["claude"] = catalog["slugs"]
        installed = version_of(run("claude", "--version"))
        if installed and catalog["version"] != installed:
            notices.append(
                f"T3's Claude catalog is from {catalog['version']}, installed is {installed}; "
                "restart T3 for a current model list"
            )
    return {name: models for name, models in live.items() if models}


def upstream_versions():
    versions = {
        "codex": version_of(run("gh", "api", "repos/openai/codex/releases/latest", "-q", ".tag_name")),
        "claude": version_of(run("npm", "view", "@anthropic-ai/claude-code", "version")),
        "grok": parsed(
            "grok update --check",
            lambda text: version_of(json.loads(text)["latestVersion"]),
            run("grok", "update", "--check", "--json"),
        ),
        # agy publishes no release feed: it self-updates, so installed is the best anchor.
        "agy": version_of(run("agy", "--version")),
        "t3": version_of(run("gh", "api", "repos/pingdotgg/t3code/releases/latest", "-q", ".tag_name")),
    }
    errors.extend(f"no version for {name}" for name, value in versions.items() if value is None)
    return versions


def installed_versions():
    installed = {name: version_of(run(name, "--version")) for name in ("codex", "claude", "grok", "agy")}
    installed["t3_server"] = version_of(run("t3", "--version"))
    errors.extend(f"no installed version for {name}" for name, value in installed.items() if value is None)
    plist = "/Applications/T3 Code (Beta).app/Contents/Info"
    if Path(plist + ".plist").exists():
        installed["t3_desktop"] = version_of(run("defaults", "read", plist, "CFBundleShortVersionString"))
        if installed["t3_desktop"] != installed["t3_server"]:
            notices.append(
                f"T3 desktop {installed['t3_desktop']} and server {installed['t3_server']} differ"
            )
    return installed


def ignored(model, patterns):
    return any(fnmatch.fnmatch(model, pattern) for pattern in patterns)


def record(report_path):
    report = json.loads(report_path.read_text())
    versions = report["upstream"]
    if report["errors"] or not all(versions.values()):
        sys.exit(f"Refusing to record a report with failures: {report['errors']}")
    ROUTER_STATE.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps({"reviewed_at": datetime.now(timezone.utc).isoformat(), "versions": versions}, indent=2) + "\n"
    )
    print(f"Recorded {versions} in {STATE_FILE}")


def model_diff(registry, live, config):
    new_models, missing_models, t3_gaps, t3_recovered = {}, {}, {}, {}
    for provider, (prefix, mixed) in PROVIDERS.items():
        if provider not in live:
            errors.append(f"no live model list for {provider}")
            continue
        routed = {model for model in registry if model.startswith(prefix)}
        relevant = {
            model
            for model in live[provider]
            if (model.startswith(prefix) or not mixed) and not ignored(model, config["ignore_live"])
        }
        new_models[provider] = sorted(relevant - routed)
        missing_models[provider] = sorted(
            model
            for model in routed - live[provider]
            if not ignored(model, config["ignore_registry"])
        )
        catalog = t3_cache(T3_CATALOGS[provider])
        if catalog is not None:
            t3_gaps[provider] = sorted(
                model
                for model in relevant - catalog["slugs"]
                if not ignored(model, config["known_t3_gaps"])
            )
            t3_recovered[provider] = sorted(
                model for model in catalog["slugs"] if ignored(model, config["known_t3_gaps"])
            )
    return new_models, missing_models, t3_gaps, t3_recovered


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, help="checkout whose registry to compare")
    parser.add_argument("--record", type=Path, metavar="REPORT", help="store a saved report's versions as reviewed")
    args = parser.parse_args()
    if args.record:
        record(args.record)
        return
    if not args.repo:
        parser.error("pass --repo or --record")
    repo = args.repo.resolve()
    config = json.loads(Path(__file__).with_name("probe-config.json").read_text())

    upstream = upstream_versions()
    try:
        reviewed = json.loads(STATE_FILE.read_text())["versions"]
    except (OSError, ValueError, KeyError, TypeError):
        reviewed = {}
    version_changes = {
        name: {"reviewed": reviewed.get(name), "upstream": value}
        for name, value in upstream.items()
        if value and value != reviewed.get(name)
    }
    new_models, missing_models, t3_gaps, t3_recovered = model_diff(
        registry_models(repo), live_models(), config
    )
    installed = installed_versions()

    master = (run("git", "-C", str(repo), "rev-parse", "origin/master") or "").strip()
    try:
        installed_commit = INSTALLED_COMMIT.read_text().strip()
    except OSError:
        installed_commit = None
    if installed_commit != master:
        notices.append(
            f"install is at {installed_commit[:7] if installed_commit else 'an unknown commit'}, origin/master is {master[:7]}; "
            "see the auto-sync.sh output"
        )

    report = {
        "first_run": not reviewed,
        "upstream": upstream,
        "version_changes": version_changes,
        "installed": installed,
        "new_models": {key: value for key, value in new_models.items() if value},
        "missing_models": {key: value for key, value in missing_models.items() if value},
        "t3_catalog_gaps": {key: value for key, value in t3_gaps.items() if value},
        "t3_gaps_recovered": {key: value for key, value in t3_recovered.items() if value},
        "notices": notices,
        "errors": errors,
    }
    report["no_change"] = not (
        version_changes
        or report["new_models"]
        or report["missing_models"]
        or report["t3_catalog_gaps"]
        or report["t3_gaps_recovered"]
        or errors
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
