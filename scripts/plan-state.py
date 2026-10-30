#!/usr/bin/env python3
"""Keep the `## Session state` block of a moonlight plan file: a fenced json block at the end of the plan.

init adds the block (never overwrites one). phase moves the flow to a phase: earlier phases become done,
later ones pending, the named one running (waiting with --waiting you, blocked with --blocked), and the
current session id is registered with its first-seen UTC time. Only the json fence is ever rewritten.

The session id is --session, else $CLAUDE_CODE_SESSION_ID, else the newest main transcript of the current
directory's project under ~/.claude/projects/.

Usage:
  plan-state.py init PLAN --flow NAME --phases a,b,c [--done a,b] [--idea PATH]
  plan-state.py phase PLAN NAME [--waiting you | --blocked] [--branch B] [--session ID]
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

FENCE = re.compile(r"^## Session state[ \t]*\n\s*```json\n(.*?)\n```", re.S | re.M)


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    """Write via a temp file and a rename, so the panel's 3 s reread never sees a truncated plan."""
    path = os.path.realpath(path)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".plan-state-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        shutil.copymode(path, tmp)
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def init(args):
    text = read(args.plan)
    if re.search(r"^## Session state[ \t]*$", text, re.M):
        print("plan-state: " + args.plan + " already has ## Session state; left as is")
        return
    phases = [p.strip() for p in args.phases.split(",") if p.strip()]
    done = [p.strip() for p in (args.done or "").split(",") if p.strip()]
    unknown = [p for p in done if p not in phases]
    if not phases or unknown:
        sys.exit("plan-state: --phases is empty or --done names unknown phases: " + ", ".join(unknown))
    state = {
        "flow": args.flow,
        "phase": None,
        "waiting": None,
        "phases": {p: "done" if p in done else "pending" for p in phases},
        "sessions": [],
        "branch": None,
        "idea": args.idea,
    }
    block = "## Session state\n\n```json\n" + json.dumps(state, indent=2) + "\n```\n"
    write(args.plan, text.rstrip("\n") + "\n\n" + block)


def current_session(explicit):
    if explicit or os.environ.get("CLAUDE_CODE_SESSION_ID"):
        return explicit or os.environ["CLAUDE_CODE_SESSION_ID"]
    encoded = re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(os.getcwd()))
    mains = sorted(glob.glob(os.path.join(os.path.expanduser("~/.claude/projects"), encoded, "*.jsonl")),
                   key=os.path.getmtime)
    return os.path.basename(mains[-1])[: -len(".jsonl")] if mains else None


def phase(args):
    text = read(args.plan)
    match = FENCE.search(text)
    if not match:
        sys.exit("plan-state: " + args.plan + " has no ## Session state block; run init first")
    try:
        state = json.loads(match.group(1))
        names = list(state["phases"])
    except (ValueError, KeyError, TypeError):
        sys.exit("plan-state: the ## Session state block of " + args.plan + " is not valid json; nothing written")
    if args.name not in names:
        sys.exit("plan-state: unknown phase {!r}; the phases are {}".format(args.name, ", ".join(names)))
    at = names.index(args.name)
    status = "waiting" if args.waiting else "blocked" if args.blocked else "running"
    state["phases"] = {n: "done" if i < at else status if i == at else "pending" for i, n in enumerate(names)}
    state["phase"] = args.name
    state["waiting"] = args.waiting
    if args.branch:
        state["branch"] = args.branch
    session = current_session(args.session)
    sessions = state.setdefault("sessions", [])
    if session is None:
        print("plan-state: no session id found; none registered", file=sys.stderr)
    elif all(s.get("id") != session for s in sessions):
        sessions.append({"id": session, "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
    write(args.plan, text[: match.start(1)] + json.dumps(state, indent=2) + text[match.end(1):])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    p_init = commands.add_parser("init", help="add ## Session state to a plan (never overwrites)")
    p_init.add_argument("plan")
    p_init.add_argument("--flow", required=True)
    p_init.add_argument("--phases", required=True, help="the flow's phases in order, comma-separated")
    p_init.add_argument("--done", help="phases already done, comma-separated")
    p_init.add_argument("--idea", help="path of the idea file")
    p_phase = commands.add_parser("phase", help="move the flow to a phase")
    p_phase.add_argument("plan")
    p_phase.add_argument("name")
    marks = p_phase.add_mutually_exclusive_group()
    marks.add_argument("--waiting", choices=["you"], help="the phase waits for the owner")
    marks.add_argument("--blocked", action="store_true", help="the phase is blocked")
    p_phase.add_argument("--branch")
    p_phase.add_argument("--session", help="session id (default: $CLAUDE_CODE_SESSION_ID, else the newest)")
    args = parser.parse_args()
    if args.command == "init":
        init(args)
    else:
        phase(args)


if __name__ == "__main__":
    main()
