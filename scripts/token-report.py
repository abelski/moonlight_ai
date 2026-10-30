#!/usr/bin/env python3
"""Sum the token usage of a Claude Code run from its session transcripts.

Reads the transcripts of one project under ~/.claude/projects/, the newest session by default, plus its
subagent transcripts. Each assistant message id is counted once, from --since onward. Timestamps must be
UTC, written as YYYY-MM-DDTHH:MM:SSZ (fractions are ignored). --json adds by_agent: one entry per transcript.

--plan PLAN takes the session ids from the plan's `## Session state` block and the time from its
`started_at`, and writes (or replaces) the plan's `## spendreport` section.

Usage:
  token-report.py [--project DIR] [--session ID ... | --all-sessions] [--since ISO_UTC] [--json]
  token-report.py [--project DIR] --plan PLAN
"""
import argparse
import glob
import json
import os
import re
import shutil
import sys
import tempfile
import time

FIELDS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")


def project_dir(path):
    encoded = re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(path))
    return os.path.join(os.path.expanduser("~/.claude/projects"), encoded)


def session_files(pdir, session_ids, all_sessions):
    mains = sorted(glob.glob(os.path.join(pdir, "*.jsonl")), key=os.path.getmtime)
    if session_ids:
        mains = [m for m in mains if os.path.basename(m)[: -len(".jsonl")] in session_ids]
    elif not all_sessions:
        mains = mains[-1:]
    files = []
    for main in mains:
        files.append(main)
        sub = os.path.join(pdir, os.path.basename(main)[: -len(".jsonl")], "subagents")
        files.extend(sorted(glob.glob(os.path.join(sub, "*.jsonl"))))
    return files


def totals(files, since):
    """Count each message id once; return the count and the token sums of each file that owns a message."""
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
                    usage_by_id[message_id] = (path, usage)
    sums = {path: {field: 0 for field in FIELDS} for path in files}
    for path, usage in usage_by_id.values():
        for field in FIELDS:
            sums[path][field] += usage.get(field) or 0
    return len(usage_by_id), sums


def billable(sums):
    return sums["input_tokens"] + sums["cache_creation_input_tokens"] + sums["output_tokens"]


def agent_row(path, sums):
    stem = os.path.basename(path)[: -len(".jsonl")]
    if os.path.basename(os.path.dirname(path)) != "subagents":
        session, label = stem, "main"
    else:
        session = os.path.basename(os.path.dirname(os.path.dirname(path)))
        try:
            with open(os.path.join(os.path.dirname(path), stem + ".meta.json"), encoding="utf-8") as handle:
                meta = json.load(handle)
        except (OSError, ValueError):
            meta = {}
        if not isinstance(meta, dict):
            meta = {}
        label = ": ".join(str(meta[k]) for k in ("agentType", "description") if meta.get(k)) or stem
    return {"session": session, "label": label, **sums, "billable_total": billable(sums)}


def report(pdir, session_ids, all_sessions, since):
    if not os.path.isdir(pdir):
        sys.exit("token-report: no transcripts for this project at " + pdir)
    files = session_files(pdir, session_ids, all_sessions)
    if not files:
        sys.exit("token-report: no session transcript found in " + pdir)
    count, per_file = totals(files, since)
    sums = {field: sum(row[field] for row in per_file.values()) for field in FIELDS}
    return {
        "transcripts": len(files),
        "messages": count,
        "since": since or "start of session",
        **sums,
        "billable_total": billable(sums),
        "by_agent": [agent_row(path, per_file[path]) for path in files],
    }


def plan_inputs(text):
    """The plan's started_at and session ids, or exit with the reason."""
    front = re.match(r"---\n(.*?)\n---\n", text, re.S)
    found = front and re.search(r"^started_at:[ \t]*(.*?)[ \t]*$", front.group(1), re.M)
    started = found.group(1).strip("'\"") if found else ""
    if started in ("", "null", "~"):
        sys.exit("token-report: the plan has no started_at; nothing written")
    block = re.search(r"^## Session state[ \t]*\n\s*```json\n(.*?)\n```", text, re.S | re.M)
    if not block:
        sys.exit("token-report: the plan has no ## Session state block; nothing written")
    try:
        state = json.loads(block.group(1))
        sessions = [s["id"] for s in state["sessions"]]
    except (ValueError, KeyError, TypeError):
        sys.exit("token-report: the plan's ## Session state block is not valid; nothing written")
    if not sessions:
        sys.exit("token-report: the plan's ## Session state lists no sessions; nothing written")
    return started, sessions


def replace_section(text, title, section):
    """Replace the `## title` section (up to the next `## ` heading) or append it at the end."""
    pattern = re.compile(r"^## {}[ \t]*\n.*?(?=^## |\Z)".format(re.escape(title)), re.S | re.M)
    match = pattern.search(text)
    if not match:
        return text.rstrip("\n") + "\n\n" + section
    tail = text[match.end():]
    return text[: match.start()] + section + ("\n" if tail else "") + tail


def write_spendreport(pdir, path):
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    started, sessions = plan_inputs(text)
    result = report(pdir, sessions, False, started)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    section = "\n".join([
        "## spendreport",
        "",
        "Counted at {} over sessions {}: everything in those sessions since {}, subagents included.".format(
            now, ", ".join(sessions), started),
        "",
        "- messages: {}".format(result["messages"]),
        "- input tokens (new): {}".format(result["input_tokens"]),
        "- cache writes: {}".format(result["cache_creation_input_tokens"]),
        "- cache reads: {}".format(result["cache_read_input_tokens"]),
        "- output tokens: {}".format(result["output_tokens"]),
        "- billable total (new + writes + output): {}".format(result["billable_total"]),
        "",
    ])
    write(path, replace_section(text, "spendreport", section))
    print("token-report: wrote ## spendreport to " + path)


def write(path, text):
    """Write via a temp file and a rename, so the panel's 3 s reread never sees a truncated plan."""
    path = os.path.realpath(path)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".token-report-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        shutil.copymode(path, tmp)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", default=os.getcwd(), help="project directory (default: current directory)")
    parser.add_argument("--session", action="append",
                        help="session id (the transcript file name without .jsonl); repeat for several")
    parser.add_argument("--all-sessions", action="store_true", help="count every session of the project")
    parser.add_argument("--since", help="count messages at or after this UTC time, YYYY-MM-DDTHH:MM:SSZ")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    parser.add_argument("--plan", help="write ## spendreport into this plan file, from its state block and started_at")
    args = parser.parse_args()

    pdir = project_dir(args.project)
    if args.plan:
        write_spendreport(pdir, args.plan)
        return
    result = report(pdir, args.session, args.all_sessions, args.since)
    if args.json:
        print(json.dumps(result, indent=2))
        return
    print("Token report (since {})".format(result["since"]))
    print("  transcripts read:           {}".format(result["transcripts"]))
    print("  assistant messages counted: {}".format(result["messages"]))
    print("  input tokens (new):         {}".format(result["input_tokens"]))
    print("  cache writes:               {}".format(result["cache_creation_input_tokens"]))
    print("  cache reads:                {}".format(result["cache_read_input_tokens"]))
    print("  output tokens:              {}".format(result["output_tokens"]))
    print("  billable total (new + writes + output): {}".format(result["billable_total"]))


if __name__ == "__main__":
    main()
