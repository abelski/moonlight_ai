#!/usr/bin/env python3
"""Sum the token usage of a Claude Code run from its session transcripts.

Reads the transcripts of one project under ~/.claude/projects/, the newest session by default, plus its
subagent transcripts. Each assistant message id is counted once, from --since onward. Timestamps must be
UTC, written as YYYY-MM-DDTHH:MM:SSZ (fractions are ignored).

Usage:
  token-report.py [--project DIR] [--session ID | --all-sessions] [--since ISO_UTC] [--json]
"""
import argparse
import glob
import json
import os
import re
import sys

FIELDS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")


def project_dir(path):
    encoded = re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(path))
    return os.path.join(os.path.expanduser("~/.claude/projects"), encoded)


def session_files(pdir, session_id, all_sessions):
    mains = sorted(glob.glob(os.path.join(pdir, "*.jsonl")), key=os.path.getmtime)
    if session_id:
        mains = [m for m in mains if os.path.basename(m) == session_id + ".jsonl"]
    elif not all_sessions:
        mains = mains[-1:]
    files = []
    for main in mains:
        files.append(main)
        sub = os.path.join(pdir, os.path.basename(main)[: -len(".jsonl")], "subagents")
        files.extend(sorted(glob.glob(os.path.join(sub, "*.jsonl"))))
    return files


def totals(files, since):
    usage_by_id = {}
    for path in files:
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if entry.get("type") != "assistant":
                    continue
                if since and entry.get("timestamp", "")[:19] < since[:19]:
                    continue
                message = entry.get("message") or {}
                usage = message.get("usage")
                message_id = message.get("id") or entry.get("uuid")
                if usage and message_id:
                    usage_by_id[message_id] = usage
    sums = {field: 0 for field in FIELDS}
    for usage in usage_by_id.values():
        for field in FIELDS:
            sums[field] += usage.get(field) or 0
    return len(usage_by_id), sums


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", default=os.getcwd(), help="project directory (default: current directory)")
    parser.add_argument("--session", help="session id (the transcript file name without .jsonl)")
    parser.add_argument("--all-sessions", action="store_true", help="count every session of the project")
    parser.add_argument("--since", help="count messages at or after this UTC time, YYYY-MM-DDTHH:MM:SSZ")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    args = parser.parse_args()

    pdir = project_dir(args.project)
    if not os.path.isdir(pdir):
        sys.exit("token-report: no transcripts for this project at " + pdir)
    files = session_files(pdir, args.session, args.all_sessions)
    if not files:
        sys.exit("token-report: no session transcript found in " + pdir)

    count, sums = totals(files, args.since)
    billable = sums["input_tokens"] + sums["cache_creation_input_tokens"] + sums["output_tokens"]
    result = {
        "transcripts": len(files),
        "messages": count,
        "since": args.since or "start of session",
        **sums,
        "billable_total": billable,
    }
    if args.json:
        print(json.dumps(result, indent=2))
        return
    print("Token report (since {})".format(result["since"]))
    print("  transcripts read:           {}".format(result["transcripts"]))
    print("  assistant messages counted: {}".format(result["messages"]))
    print("  input tokens (new):         {}".format(sums["input_tokens"]))
    print("  cache writes:               {}".format(sums["cache_creation_input_tokens"]))
    print("  cache reads:                {}".format(sums["cache_read_input_tokens"]))
    print("  output tokens:              {}".format(sums["output_tokens"]))
    print("  billable total (new + writes + output): {}".format(billable))


if __name__ == "__main__":
    main()
