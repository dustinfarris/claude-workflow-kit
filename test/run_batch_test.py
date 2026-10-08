#!/usr/bin/env python3
"""Tests for tools/run-batch.py, run by test/hooks_test.sh.

Fixtures under test/fixtures/run-batch/ are copied from bear-cub's
weather-indicator chain, never hand-built:
  closed/…/PLAN.org            355a69b  (Batch 1 with its gate record)
  open/…/PLAN.org              fb02740  (Stories 01–03 DONE, 04–05 TODO)
  open/…/story-04-….org        9bb9999  (ticked by its close-out)
  open/…/story-05-….org        354a999  (as written, nothing ticked)
  */CLAUDE.md                  the first three lines of bear-cub's CLAUDE.md
Story 04 ticked while its PLAN heading still reads TODO is the state an
implementer that self-triggers story-closeout leaves behind.

Each test copies a fixture into a temp git repo. The Claude invocation is
the module's invoke() function, replaced here by a scripted stub.
"""
import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, "test", "fixtures", "run-batch")
INIT = "docs/2026-10-07-weather-indicator"
S04 = f"{INIT}/stories/story-04-shows-weather-flag.org"
S05 = f"{INIT}/stories/story-05-kiosk-weather-row.org"

spec = importlib.util.spec_from_file_location("run_batch", os.path.join(ROOT, "tools", "run-batch.py"))
rb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rb)

# Test-side git only: the machine's global commit-msg linter and signing
# have no business in a throwaway fixture repo.
GIT = ["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
       "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid"]


def git(repo, *args):
    subprocess.run(GIT + ["-C", repo] + list(args), check=True, capture_output=True)


def tick(repo, rel):
    p = os.path.join(repo, rel)
    with open(p) as f:
        text = f.read()
    with open(p, "w") as f:
        f.write(text.replace("** [ ]", "** [X]"))


def mark_done(repo, story_rel):
    p = os.path.join(repo, INIT, "PLAN.org")
    name = os.path.basename(story_rel)
    with open(p) as f:
        text = f.read()
    with open(p, "w") as f:
        f.write(re.sub(r"^\*\* TODO (\[\[file:stories/" + re.escape(name) + ")", r"** DONE \1", text, flags=re.M))


def reply(result, sid="sess-1", **extra):
    d = {"type": "result", "subtype": "success", "is_error": False, "session_id": sid, "result": result}
    d.update(extra)
    return json.dumps(d)


class Stub:
    """Scripted stand-in for rb.invoke: each step is (effect, stdout)."""

    def __init__(self, repo, steps):
        self.repo, self.steps, self.calls = repo, list(steps), []

    def __call__(self, argv, cwd):
        self.calls.append(argv)
        effect, out = self.steps.pop(0)
        if effect:
            effect(self.repo)
        return 0, out, ""

    def prompts(self):
        return [a[a.index("-p") + 1] for a in self.calls]


class Base(unittest.TestCase):
    fixture = "open"

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(os.path.join(self.home, ".claude"))
        with open(os.path.join(self.home, ".claude", "settings.json"), "w") as f:
            json.dump({"permissions": {"defaultMode": "auto"}}, f)
        self.repo = os.path.join(self.tmp, "repo")
        shutil.copytree(os.path.join(FIX, self.fixture), self.repo)
        git(self.repo, "init", "-q")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "fixture")
        self._home, os.environ["HOME"] = os.environ.get("HOME"), self.home
        self._invoke = rb.invoke

    def tearDown(self):
        rb.invoke = self._invoke
        os.environ["HOME"] = self._home
        shutil.rmtree(self.tmp)

    def run_driver(self, *flags):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = rb.main(["--repo", self.repo] + list(flags))
        return rc, out.getvalue() + err.getvalue()

    def stub(self, steps):
        s = Stub(self.repo, steps)
        rb.invoke = s
        return s

    def commit_all(self, repo):
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "story")


class OpenBatch(Base):
    def test_open_batch_found_and_stories_ordered(self):
        batch = rb.open_batch(rb.read(os.path.join(self.repo, INIT, "PLAN.org")))
        self.assertEqual(batch.title, "Batch 1 — Weather indicator")
        self.assertEqual([s.path for s in batch.todo(INIT)], [S04, S05])

    def test_initiative_from_claude_md(self):
        self.assertEqual(rb.active_initiative(self.repo), INIT)

    def test_open_items_counted_and_unparseable_story_refused(self):
        self.assertEqual(rb.open_items(os.path.join(self.repo, S04)), 0)
        self.assertEqual(rb.open_items(os.path.join(self.repo, S05)), 15)
        blank = os.path.join(self.repo, "blank.org")
        with open(blank, "w") as f:
            f.write("* Acceptance Criteria\nnothing here\n")
        with self.assertRaises(rb.Refusal):
            rb.open_items(blank)

    def test_dry_run_never_invokes_and_shows_closeout_skipped(self):
        s = self.stub([])
        rc, out = self.run_driver("--dry-run")
        self.assertEqual(rc, 0, out)
        self.assertEqual(s.calls, [])
        self.assertRegex(out, r"story-04-shows-weather-flag\.org[\s\S]*closeout\s+skip")
        self.assertIn("first stage: update-design (story-04-shows-weather-flag)", out)
        self.assertLess(out.index("story-04"), out.index("story-05"))
        self.assertIn("permission mode: auto", out)

    def test_self_ticked_story_skips_closeout_and_batch_runs_to_gate(self):
        def commit(repo):
            self.commit_all(repo)
        s = self.stub([
            (lambda r: mark_done(r, S04), reply("Plan marked DONE.\nRESULT: done", "a")),
            (commit, reply("Committed.\nRESULT: done", "a")),
            (lambda r: open(os.path.join(r, "lib.ex"), "w").write("x"), reply("Built.\nRESULT: done", "b")),
            (lambda r: tick(r, S05), reply("All ticked.\nRESULT: done", "b")),
            (lambda r: mark_done(r, S05), reply("Plan marked DONE.\nRESULT: done", "b")),
            (commit, reply("Committed.\nRESULT: done", "b")),
        ])
        rc, out = self.run_driver()
        self.assertEqual(rc, 0, out)
        self.assertEqual(s.prompts(), [
            "/workflow-kit:update-design", "commit",
            f"implement @{S05}", "/workflow-kit:story-closeout", "/workflow-kit:update-design", "commit"])
        self.assertIn("phase-close is next", out)
        # one session per story: the first stage starts it, the rest resume it
        self.assertNotIn("--resume", s.calls[0])
        self.assertEqual(s.calls[1][s.calls[1].index("--resume") + 1], "a")
        self.assertNotIn("--resume", s.calls[2])
        self.assertTrue(all(c[c.index("--resume") + 1] == "b" for c in s.calls[3:]))

    def test_driver_never_commits(self):
        # the session commits on the "commit" prompt; the driver only reads git
        real, seen = rb.subprocess.run, []

        def spy(argv, *a, **k):
            if argv[:1] == ["git"]:
                seen.append(argv)
            return real(argv, *a, **k)
        head = subprocess.run(["git", "-C", self.repo, "rev-parse", "HEAD"], capture_output=True, text=True).stdout
        rb.subprocess.run = spy
        try:
            s = self.stub([
                (lambda r: mark_done(r, S04), reply("RESULT: done", "a")),
                (None, reply("Committed.\nRESULT: done", "a")),  # says so, commits nothing
            ])
            rc, out = self.run_driver()
        finally:
            rb.subprocess.run = real
        self.assertNotEqual(rc, 0)
        self.assertEqual(s.prompts(), ["/workflow-kit:update-design", "commit"])
        self.assertIn("STOP at commit", out)
        self.assertEqual(head, subprocess.run(["git", "-C", self.repo, "rev-parse", "HEAD"], capture_output=True, text=True).stdout)
        self.assertTrue(seen)
        self.assertEqual({a[a.index("-C") + 2] for a in seen}, {"status"})

    def test_stops_before_phase_close(self):
        for story in (S04, S05):
            tick(self.repo, story)
            mark_done(self.repo, story)
        self.commit_all(self.repo)
        s = self.stub([])
        rc, out = self.run_driver()
        self.assertEqual(rc, 0, out)
        self.assertEqual(s.calls, [])
        self.assertIn("phase-close is next, and it is the human's to run", out)
        self.assertNotIn("phase-close", " ".join(rb.PROMPTS.values()))

    def test_argv_shape_and_never_a_bypass(self):
        s = self.stub([(None, reply("RESULT: blocked — nothing", "a"))])
        self.run_driver()
        argv = s.calls[0]
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "auto")
        self.assertEqual(argv[argv.index("--output-format") + 1], "json")
        self.assertIn("RESULT: done", argv[argv.index("--append-system-prompt") + 1])
        flags = argv[:argv.index("--append-system-prompt")] + argv[argv.index("--append-system-prompt") + 2:]
        source = rb.read(os.path.join(ROOT, "tools", "run-batch.py"))
        for bad in ("dangerously", "bypassPermissions", "no-gpg-sign", "gpgsign"):
            self.assertNotIn(bad, " ".join(flags))
        for bad in ("dangerously", "no-gpg-sign", "gpgsign"):
            self.assertNotIn(bad, source)

    def test_false_predicate_after_stage_stops_despite_done(self):
        s = self.stub([(None, reply("I updated the design.\nRESULT: done", "a"))])
        rc, out = self.run_driver()
        self.assertNotEqual(rc, 0)
        self.assertEqual(len(s.calls), 1)
        for want in ("update-design", "story-04-shows-weather-flag", "claude --resume a", "I updated the design."):
            self.assertIn(want, out)

    def test_blocked_result_stops_with_true_predicate(self):
        s = self.stub([(lambda r: mark_done(r, S04), reply("RESULT: blocked — D145 needs a ruling", "a"))])
        rc, out = self.run_driver()
        self.assertNotEqual(rc, 0)
        self.assertEqual(len(s.calls), 1)
        self.assertIn("D145 needs a ruling", out)

    def test_missing_or_decorated_result_line_is_a_stop(self):
        for text in ("Done.", "**RESULT: done**"):
            with self.subTest(text=text):
                s = self.stub([(lambda r: mark_done(r, S04), reply(text, "a"))])
                rc, _ = self.run_driver()
                self.assertNotEqual(rc, 0)
                self.assertEqual(len(s.calls), 1)
                git(self.repo, "checkout", "-q", "--", ".")

    def test_lost_connection_gets_one_continue(self):
        lost = reply("API Error: Connection lost mid-response. The response above may be incomplete.", "a", is_error=True)
        s = self.stub([
            (None, lost),
            (lambda r: mark_done(r, S04), reply("RESULT: done", "a")),
            (None, lost),
            (None, lost),
        ])
        rc, out = self.run_driver()
        self.assertNotEqual(rc, 0)
        self.assertEqual(s.prompts(), ["/workflow-kit:update-design", "continue", "commit", "continue"])
        self.assertEqual(s.calls[1][s.calls[1].index("--resume") + 1], "a")

    def test_dirty_tree_refused_before_a_story_starts(self):
        tick(self.repo, S04)  # nothing left for 04, so the next start is 05's implement
        mark_done(self.repo, S04)
        self.commit_all(self.repo)
        with open(os.path.join(self.repo, "stray.txt"), "w") as f:
            f.write("x")
        s = self.stub([])
        rc, out = self.run_driver()
        self.assertNotEqual(rc, 0)
        self.assertEqual(s.calls, [])
        self.assertIn("stray.txt", out)
        # it says what to do, not only what it found
        self.assertIn("finish closeout in the resumed session", out)
        self.assertIn("then rerun run-batch.py", out)
        self.assertIn("story-05-kiosk-weather-row.org", out)

    def test_dirty_tree_allowed_when_resuming_mid_story(self):
        with open(os.path.join(self.repo, "lib.ex"), "w") as f:
            f.write("uncommitted code from the stopped session")
        s = self.stub([(None, reply("RESULT: blocked — stop here", "a"))])
        self.run_driver()
        self.assertEqual(s.prompts(), ["/workflow-kit:update-design"])

    def test_bypass_permission_default_refused(self):
        with open(os.path.join(self.home, ".claude", "settings.json"), "w") as f:
            json.dump({"permissions": {"defaultMode": "bypassPermissions"}}, f)
        s = self.stub([])
        rc, out = self.run_driver()
        self.assertNotEqual(rc, 0)
        self.assertEqual(s.calls, [])
        self.assertIn("bypassPermissions", out)

    def test_project_permission_mode_wins_over_user(self):
        os.makedirs(os.path.join(self.repo, ".claude"), exist_ok=True)
        with open(os.path.join(self.repo, ".claude", "settings.local.json"), "w") as f:
            json.dump({"permissions": {"defaultMode": "acceptEdits"}}, f)
        self.assertEqual(rb.permission_mode(self.repo)[0], "acceptEdits")

    def test_dev_server_not_answering_refused(self):
        with open(os.path.join(self.repo, ".mcp.json"), "w") as f:
            json.dump({"mcpServers": {"tidewave": {"type": "http", "url": "http://127.0.0.1:1/tidewave/mcp"}}}, f)
        self.commit_all(self.repo)
        s = self.stub([])
        rc, out = self.run_driver()
        self.assertNotEqual(rc, 0)
        self.assertEqual(s.calls, [])
        self.assertIn("127.0.0.1:1/tidewave/mcp", out)


class ClosedBatch(Base):
    fixture = "closed"

    def test_closed_batch_refused(self):
        s = self.stub([])
        for flags in ((), ("--dry-run",)):
            rc, out = self.run_driver(*flags)
            self.assertNotEqual(rc, 0)
            self.assertIn("no open batch", out)
        self.assertEqual(s.calls, [])


if __name__ == "__main__":
    unittest.main()
