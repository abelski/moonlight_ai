"""Tests for scripts/plan-state.py, run as a subprocess with HOME pointed at a temp dir."""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "plan-state.py")
FENCE = re.compile(r"^## Session state[ \t]*\n\s*```json\n(.*?)\n```", re.S | re.M)

PLAN = """---
kind: feature
status: in_progress
started_at: 2026-10-30T10:00:00Z
---

# Plan

## Implementation

- [ ] 1. thing
"""


class PlanStateTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = os.path.join(tmp.name, "home")
        self.project = os.path.join(tmp.name, "project")
        os.makedirs(self.home)
        os.makedirs(self.project)
        self.plan = os.path.join(self.project, "plan.md")
        self.write(PLAN)

    def write(self, text):
        with open(self.plan, "w", encoding="utf-8") as handle:
            handle.write(text)

    def text(self):
        with open(self.plan, encoding="utf-8") as handle:
            return handle.read()

    def state(self):
        return json.loads(FENCE.search(self.text()).group(1))

    def run_script(self, *args, env_session=None):
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_SESSION_ID"}
        env["HOME"] = self.home
        if env_session:
            env["CLAUDE_CODE_SESSION_ID"] = env_session
        return subprocess.run([sys.executable, SCRIPT, *args], env=env, cwd=self.project, capture_output=True,
                              text=True)

    def ok(self, *args, **kwargs):
        done = self.run_script(*args, **kwargs)
        self.assertEqual(done.returncode, 0, done.stderr)
        return done

    def init(self, phases="a,b,c,d", *extra):
        return self.ok("init", self.plan, "--flow", "moonlight-fast", "--phases", phases, *extra)

    def test_init_adds_block_once(self):
        self.init("a,b,c,d", "--done", "a", "--idea", "plans/ideas/idea_1_x.md")
        state = self.state()
        self.assertEqual(state["flow"], "moonlight-fast")
        self.assertEqual(state["phases"], {"a": "done", "b": "pending", "c": "pending", "d": "pending"})
        self.assertEqual(list(state["phases"]), ["a", "b", "c", "d"])
        self.assertEqual(state["idea"], "plans/ideas/idea_1_x.md")
        self.assertEqual(state["sessions"], [])
        self.assertTrue(self.text().startswith(PLAN.rstrip("\n")))
        before = self.text()
        self.init("x,y")
        self.assertEqual(self.text(), before)

    def test_init_without_frontmatter(self):
        self.write("# Plan\n\n- [ ] 1. thing\n")
        self.init()
        self.assertEqual(self.text().count("## Session state"), 1)
        self.assertEqual(self.state()["phases"]["a"], "pending")

    def test_phase_orders_and_resets_later_phases(self):
        self.init()
        self.ok("phase", self.plan, "c", "--session", "s1")
        state = self.state()
        self.assertEqual(state["phase"], "c")
        self.assertEqual(state["phases"], {"a": "done", "b": "done", "c": "running", "d": "pending"})
        self.ok("phase", self.plan, "d", "--session", "s1")
        self.ok("phase", self.plan, "b", "--session", "s1")
        self.assertEqual(self.state()["phases"], {"a": "done", "b": "running", "c": "pending", "d": "pending"})

    def test_waiting_and_blocked(self):
        self.init()
        self.ok("phase", self.plan, "b", "--waiting", "you", "--session", "s1")
        state = self.state()
        self.assertEqual((state["phases"]["b"], state["waiting"]), ("waiting", "you"))
        self.ok("phase", self.plan, "c", "--blocked", "--branch", "feat/1-x", "--session", "s1")
        state = self.state()
        self.assertEqual((state["phases"]["c"], state["waiting"]), ("blocked", None))
        self.assertEqual(state["phases"]["b"], "done")
        self.assertEqual(state["branch"], "feat/1-x")
        self.ok("phase", self.plan, "c", "--session", "s1")
        self.assertEqual(self.state()["branch"], "feat/1-x")

    def test_session_registered_once(self):
        self.init()
        self.ok("phase", self.plan, "a", "--session", "s1")
        self.ok("phase", self.plan, "b", "--session", "s1")
        sessions = self.state()["sessions"]
        self.assertEqual([s["id"] for s in sessions], ["s1"])
        self.assertRegex(sessions[0]["started_at"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.ok("phase", self.plan, "c", env_session="s2")
        self.assertEqual([s["id"] for s in self.state()["sessions"]], ["s1", "s2"])
        self.assertEqual(self.state()["sessions"][0], sessions[0])

    def test_session_falls_back_to_newest_transcript(self):
        encoded = re.sub(r"[^A-Za-z0-9]", "-", os.path.realpath(self.project))
        pdir = os.path.join(self.home, ".claude", "projects", encoded)
        os.makedirs(pdir)
        for mtime, sid in ((1_700_000_000, "older"), (1_700_000_100, "newest")):
            path = os.path.join(pdir, sid + ".jsonl")
            open(path, "w").close()
            os.utime(path, (mtime, mtime))
        self.init()
        self.ok("phase", self.plan, "a")
        self.assertEqual([s["id"] for s in self.state()["sessions"]], ["newest"])

    def test_neighbouring_sections_untouched(self):
        self.init()
        text = self.text() + "\n## Blocked\n\n- item 3: tests fail\n\n## Review\n\n- blocker: x\n"
        self.write(text)
        self.ok("phase", self.plan, "c", "--waiting", "you", "--session", "s1")
        after = self.text()
        self.assertNotEqual(after, text)
        self.assertEqual(FENCE.sub("FENCE", after), FENCE.sub("FENCE", text))

    def test_writes_replace_the_file(self):
        # a reader never sees a truncated plan: each write lands as a new file, renamed over the old one
        os.chmod(self.plan, 0o640)
        for args in (("init", self.plan, "--flow", "f", "--phases", "a,b"), ("phase", self.plan, "b", "--session", "s1")):
            before = os.stat(self.plan).st_ino
            self.ok(*args)
            self.assertNotEqual(os.stat(self.plan).st_ino, before, args[0])
            self.assertEqual(os.stat(self.plan).st_mode & 0o777, 0o640, args[0])
            self.assertEqual(os.listdir(self.project), ["plan.md"], args[0])

    def test_errors_write_nothing(self):
        before = self.text()
        self.assertNotEqual(self.run_script("phase", self.plan, "a", "--session", "s1").returncode, 0)
        self.assertEqual(self.text(), before)
        self.init()
        before = self.text()
        done = self.run_script("phase", self.plan, "nope", "--session", "s1")
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("plan-state:", done.stderr)
        self.assertEqual(self.text(), before)
        self.write(before.replace('"flow"', "flow"))
        broken = self.text()
        self.assertNotEqual(self.run_script("phase", self.plan, "a", "--session", "s1").returncode, 0)
        self.assertEqual(self.text(), broken)


if __name__ == "__main__":
    unittest.main()
