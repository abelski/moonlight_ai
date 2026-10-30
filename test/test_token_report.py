"""Tests for scripts/token-report.py, run as a subprocess with HOME pointed at a temp dir."""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "token-report.py")


def assistant(message_id, timestamp, inp=1, writes=10, reads=100, out=2):
    usage = {"input_tokens": inp, "cache_creation_input_tokens": writes, "cache_read_input_tokens": reads,
             "output_tokens": out}
    return {"type": "assistant", "timestamp": timestamp, "message": {"id": message_id, "usage": usage}}


class Fixture:
    """A temp HOME with one project folder of transcripts, and the project dir itself."""

    def __init__(self, test):
        tmp = tempfile.TemporaryDirectory()
        test.addCleanup(tmp.cleanup)
        self.home = os.path.join(tmp.name, "home")
        self.project = os.path.join(tmp.name, "project")
        os.makedirs(self.project)
        encoded = re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(self.project))
        self.pdir = os.path.join(self.home, ".claude", "projects", encoded)
        os.makedirs(self.pdir)
        self.mtime = 1_700_000_000

    def write(self, path, entries):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(json.dumps(entry) + "\n")
        self.mtime += 10  # later writes are newer, so "newest session" is deterministic
        os.utime(path, (self.mtime, self.mtime))

    def session(self, sid, entries):
        self.write(os.path.join(self.pdir, sid + ".jsonl"), entries)

    def subagent(self, sid, agent_id, entries, meta=None):
        sub = os.path.join(self.pdir, sid, "subagents")
        self.write(os.path.join(sub, "agent-{}.jsonl".format(agent_id)), entries)
        if meta is not None:
            with open(os.path.join(sub, "agent-{}.meta.json".format(agent_id)), "w", encoding="utf-8") as handle:
                json.dump(meta, handle)

    def run(self, *args):
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_SESSION_ID"}
        env["HOME"] = self.home
        return subprocess.run([sys.executable, SCRIPT, "--project", self.project, *args], env=env,
                              capture_output=True, text=True)

    def report(self, *args):
        done = self.run(*args, "--json")
        assert done.returncode == 0, done.stderr
        return json.loads(done.stdout)


PLAN = """---
kind: feature
started_at: {started}
---

# Plan

## Implementation

- [x] 1. thing

## Session state

```json
{state}
```
"""


def plan_text(started="2026-10-30T10:00:00Z", sessions=("s1",)):
    state = {"flow": "moonlight-fast", "phase": "spendreport", "waiting": None,
             "phases": {"implement": "done", "spendreport": "running"},
             "sessions": [{"id": s, "started_at": "2026-10-30T10:00:00Z"} for s in sessions],
             "branch": "feat/1-x", "idea": None}
    return PLAN.format(started=started, state=json.dumps(state, indent=2))


class TokenReportTest(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture(self)

    def test_default_reads_newest_session_and_prints_text(self):
        self.fx.session("old", [assistant("a", "2026-10-30T10:00:00Z")])
        self.fx.session("new", [assistant("b", "2026-10-30T10:00:00Z"), assistant("c", "2026-10-30T10:00:01Z")])
        done = self.fx.run()
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("Token report", done.stdout)
        self.assertIn("assistant messages counted: 2", done.stdout)
        self.assertEqual(self.fx.report("--all-sessions")["messages"], 3)

    def test_repeated_session_counts_each_listed_session(self):
        self.fx.session("s1", [assistant("a", "2026-10-30T10:00:00Z")])
        self.fx.session("s2", [assistant("b", "2026-10-30T10:00:00Z")])
        self.fx.session("s3", [assistant("c", "2026-10-30T10:00:00Z")])
        result = self.fx.report("--session", "s1", "--session", "s2")
        self.assertEqual(result["messages"], 2)
        self.assertEqual(result["transcripts"], 2)
        self.assertEqual(self.fx.report("--session", "s3", "--all-sessions")["messages"], 1)

    def test_since_skips_earlier_messages(self):
        self.fx.session("s1", [assistant("a", "2026-10-30T09:59:59Z"), assistant("b", "2026-10-30T10:00:00.500Z")])
        result = self.fx.report("--session", "s1", "--since", "2026-10-30T10:00:00Z")
        self.assertEqual(result["messages"], 1)

    def test_duplicate_message_id_counted_once(self):
        self.fx.session("s1", [assistant("a", "2026-10-30T10:00:00Z", out=1),
                               assistant("a", "2026-10-30T10:00:01Z", out=7)])
        result = self.fx.report("--session", "s1")
        self.assertEqual(result["messages"], 1)
        self.assertEqual(result["output_tokens"], 7)
        self.assertEqual(len(result["by_agent"]), 1)

    def test_by_agent_labels_and_sums(self):
        self.fx.session("s1", [assistant("m1", "2026-10-30T10:00:00Z", inp=3)])
        self.fx.subagent("s1", "abc", [assistant("x1", "2026-10-30T10:00:00Z", inp=5, out=9)],
                         meta={"agentType": "Explore", "description": "find files", "finished": True})
        self.fx.subagent("s1", "nometa", [assistant("y1", "2026-10-30T10:00:00Z", writes=50)])
        self.fx.session("s2", [assistant("m2", "2026-10-30T10:00:00Z", reads=7)])
        result = self.fx.report("--session", "s1", "--session", "s2")
        rows = {(row["session"], row["label"]): row for row in result["by_agent"]}
        self.assertEqual(set(rows), {("s1", "main"), ("s1", "Explore: find files"), ("s1", "agent-nometa"),
                                     ("s2", "main")})
        explore = rows[("s1", "Explore: find files")]
        self.assertEqual((explore["input_tokens"], explore["output_tokens"]), (5, 9))
        self.assertEqual(explore["billable_total"], 5 + 10 + 9)
        for field in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens",
                      "billable_total"):
            self.assertEqual(sum(row[field] for row in result["by_agent"]), result[field], field)

    def test_plan_writes_then_replaces_spendreport(self):
        self.fx.session("s1", [assistant("old", "2026-10-30T09:00:00Z"), assistant("a", "2026-10-30T10:00:01Z")])
        self.fx.session("s2", [assistant("b", "2026-10-30T11:00:00Z")])
        plan = os.path.join(self.fx.project, "plan.md")
        with open(plan, "w", encoding="utf-8") as handle:
            handle.write(plan_text(sessions=("s1", "s2")))

        done = self.fx.run("--plan", plan)
        self.assertEqual(done.returncode, 0, done.stderr)
        text = open(plan, encoding="utf-8").read()
        self.assertEqual(text.count("## spendreport"), 1)
        expected = self.fx.report("--session", "s1", "--session", "s2", "--since", "2026-10-30T10:00:00Z")
        self.assertIn("messages: {}".format(expected["messages"]), text)
        self.assertIn("billable total (new + writes + output): {}".format(expected["billable_total"]), text)
        self.assertIn("since 2026-10-30T10:00:00Z", text)
        self.assertIn("```json", text)  # the state block is kept

        self.fx.session("s2", [assistant("b", "2026-10-30T11:00:00Z"), assistant("c", "2026-10-30T11:00:01Z")])
        done = self.fx.run("--plan", plan)
        self.assertEqual(done.returncode, 0, done.stderr)
        text = open(plan, encoding="utf-8").read()
        self.assertEqual(text.count("## spendreport"), 1)
        self.assertIn("messages: 3", text)
        self.assertIn("## Session state", text)

    def test_plan_write_replaces_the_file(self):
        # a reader never sees a truncated plan: the new text lands as a new file, renamed over the old one
        self.fx.session("s1", [assistant("a", "2026-10-30T10:00:01Z")])
        plan = os.path.join(self.fx.project, "plan.md")
        with open(plan, "w", encoding="utf-8") as handle:
            handle.write(plan_text())
        os.chmod(plan, 0o640)
        before = os.stat(plan).st_ino
        done = self.fx.run("--plan", plan)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertNotEqual(os.stat(plan).st_ino, before)
        self.assertEqual(os.stat(plan).st_mode & 0o777, 0o640)
        self.assertEqual(os.listdir(self.fx.project), ["plan.md"])
        self.assertIn("## spendreport", open(plan, encoding="utf-8").read())

    def test_plan_errors_write_nothing(self):
        self.fx.session("s1", [assistant("a", "2026-10-30T10:00:01Z")])
        cases = {
            "no state block": "---\nstarted_at: 2026-10-30T10:00:00Z\n---\n\n# Plan\n",
            "no sessions": plan_text(sessions=()),
            "started_at null": plan_text(started="null"),
            "corrupt state": plan_text().replace('"flow"', 'flow'),
        }
        for name, content in cases.items():
            with self.subTest(name):
                plan = os.path.join(self.fx.project, "plan.md")
                with open(plan, "w", encoding="utf-8") as handle:
                    handle.write(content)
                done = self.fx.run("--plan", plan)
                self.assertNotEqual(done.returncode, 0)
                self.assertIn("token-report:", done.stderr)
                self.assertEqual(open(plan, encoding="utf-8").read(), content)


if __name__ == "__main__":
    unittest.main()
