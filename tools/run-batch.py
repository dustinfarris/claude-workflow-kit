#!/usr/bin/env python3
"""run-batch — run the open batch's stories through their four stages.

Run from a consuming repo's root once the stories and PLAN.org exist. For
every story still TODO in the open batch, in PLAN order, it runs one headless
Claude Code session through the stages below, resuming that session by id for
each stage, and stops before phase-close.

  implement      implement @<story path>        runs while the story has an open item
  closeout       /workflow-kit:story-closeout   done: no [ ] item under AC or DoD
  update-design  /workflow-kit:update-design    done: the PLAN heading reads DONE
  commit         commit                         done: git status --porcelain is empty

A stage runs only when its predicate is false, and its predicate is re-checked
afterwards. Anything other than a final "RESULT: done" line plus a true
predicate is a stop: the driver prints the session id and exits non-zero, and
the human resumes that session (claude --resume <id>), answers, and reruns the
driver, which picks up at the first false predicate. It never answers a
question, never retries a stop with another prompt, and sends "continue" once
only for a connection lost mid-response. A stage with no result within
--stage-timeout minutes (default 60) is killed and is a stop: in -p mode a
step waiting on a permission prompt would otherwise hang without a word.

The Active initiative: line is read from CLAUDE.local.md only.
When the chain documents are git-ignored, the commit prompt asks for the code
commit only, and a commit stage that leaves a newly tracked ignored path (a
force-add) is a stop.

It refuses with no open batch, a dirty tree before a story's implement stage,
a Tidewave dev server not answering, or a bypassPermissions default. The
permission mode is the human's interactive default (permissions.defaultMode).

A --plugin-dir PATH (repeatable) is passed to every turn and printed in the
resume line, for a plugin loaded from a local checkout instead of a marketplace.

Usage:
  run-batch.py [--repo PATH] [--stage-timeout MINUTES] [--plugin-dir PATH]... [--dry-run]

Design: docs/2026-10-08-batch-driver-design.org in the kit.
Python 3 standard library only.
"""
import argparse
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import uuid
import urllib.error
import urllib.request

STAGES = ("implement", "closeout", "update-design", "commit")
PROMPTS = {
    "closeout": "/workflow-kit:story-closeout",
    "update-design": "/workflow-kit:update-design",
    "commit": "commit",
}
CONTINUE = "continue"
CLAUDE = ["claude"]
STAGE_TIMEOUT_MIN = 60.0  # wall clock per stage; a -p step waiting on a permission prompt would otherwise hang
DONE_LINE = "RESULT: done"
# The two shapes seen, both in interactive transcripts: "lost" (CLI, bear-cub
# weather-indicator Story 02) and "closed" (desktop). No -p session on record
# has hit one, so the JSON form is unverified; anything else is a stop.
LOST_RE = re.compile(r"^API Error: Connection (lost|closed) mid-response\b")

SYSTEM_PROMPT = """\
This session is driven by tools/run-batch.py, a script, not a person. It sends the batch's four prompts for one story in turn (implement, /workflow-kit:story-closeout, /workflow-kit:update-design, commit), and nobody reads your messages between them. Every skill's STOP still holds.

End every final message with exactly one line of plain text, no bold, no backticks, no quoting:
RESULT: done
or
RESULT: blocked — <what the human must decide>

Write RESULT: done only when the turn reached its expected outcome. When anything needs a human — a question, a ruling, a STOP, a failure you cannot fix inside the stage's own scope — do not guess and do not ask in the middle of the turn: stop, say what is needed, and end with RESULT: blocked. A blocked turn is the correct result whenever a person would otherwise have been asked. The script checks the files after each turn, so a turn that says done without its artifact is a stop anyway.

Expected outcome of each turn:
- implement: the story's code and tests written and the repo's verify command green.
- /workflow-kit:story-closeout: every Acceptance Criteria and Definition of Done item ticked from the verifier's pass, or a named item the human must rule on (blocked).
- /workflow-kit:update-design: the story's PLAN heading marked DONE, and a DESIGN body edit only together with its Decision Log entry and Advisory.
- commit: a code commit, then a doc-only commit, and a clean working tree; only the code commit when the prompt says the repo git-ignores the chain documents. A commit that cannot be signed is blocked; never bypass signing.
- continue: finish the turn the lost connection interrupted, with its expected outcome.

Never stage a path git ignores: no git add -f, no git add --force, no editing .gitignore or .git/info/exclude to get a file in. What a repo keeps out of its history stays out. If a stage seems to need an ignored file committed, end with RESULT: blocked and name the file."""


class Refusal(Exception):
    """A precondition the driver will not work around."""


class StageTimeout(Exception):
    """A stage produced no result within the per-stage limit."""


def read(path):
    with open(path) as f:
        return f.read()


# --- the chain -------------------------------------------------------------

def active_initiative(repo):
    """The initiative directory named by CLAUDE.local.md's Active initiative: line.
    CLAUDE.md is read only to say the line must move when it is still there."""
    line = re.compile(r"^Active initiative:\s*(\S+)", re.M)
    local, shared = (os.path.join(repo, n) for n in ("CLAUDE.local.md", "CLAUDE.md"))
    m = line.search(read(local)) if os.path.isfile(local) else None
    if not m:
        if os.path.isfile(shared) and line.search(read(shared)):
            raise Refusal("the Active initiative: line is in CLAUDE.md; move it to CLAUDE.local.md, where the chain is resolved from")
        if not os.path.isfile(local):
            raise Refusal("no CLAUDE.local.md, so no Active initiative: line to resolve the chain from")
    if not m or m.group(1).rstrip(".") == "none":
        raise Refusal("CLAUDE.local.md names no active initiative")
    init = m.group(1).rstrip("/")
    if not os.path.isfile(os.path.join(repo, init, "PLAN.org")):
        raise Refusal(f"no PLAN.org in the active initiative {init}/")
    return init


STORY_RE = re.compile(r"^\*\* (TODO|DONE) \[\[file:([^\]]+)\]")


class Story:
    def __init__(self, status, link):
        self.status, self.link = status, link
        self.name = os.path.basename(link)

    def rel(self, init):
        return os.path.normpath(os.path.join(init, self.link))


class Batch:
    def __init__(self, title):
        self.title, self.stories, self.gated = title, [], False

    def todo(self, init):
        out = [s for s in self.stories if s.status == "TODO"]
        for s in out:
            s.path = s.rel(init)
        return out


def batches(text):
    """Top-level headings that carry stories, each with its gate state."""
    found, cur, in_body = [], None, False
    for line in text.splitlines():
        if line.startswith("* "):
            cur, in_body = Batch(line[2:].strip()), True
            found.append(cur)
        elif line.startswith("** "):
            in_body = False
            m = STORY_RE.match(line)
            if cur is not None and m:
                cur.stories.append(Story(m.group(1), m.group(2)))
        elif cur is not None and in_body and line.strip() == ":LOGBOOK:":
            # a LOGBOOK on the batch heading itself is the gate record
            cur.gated = True
    return [b for b in found if b.stories]


def open_batch(text):
    ungated = [b for b in batches(text) if not b.gated]
    if not ungated:
        raise Refusal("no open batch: every batch heading in PLAN.org has a gate record")
    if len(ungated) > 1:
        raise Refusal("more than one batch without a gate record: " + "; ".join(b.title for b in ungated)
                      + ". At most one batch is open at a time; gate the earlier one first")
    return ungated[0]


SECTIONS = ("Acceptance Criteria", "Definition of Done")


def open_items(path):
    """Number of [ ] items under AC and DoD. No items at all is a misread, not a pass."""
    section, items, unticked = None, 0, 0
    for line in read(path).splitlines():
        if line.startswith("* "):
            section = line[2:].strip()
        elif section in SECTIONS:
            m = re.match(r"^\*\* \[([ X-])\]", line)
            if m:
                items += 1
                unticked += m.group(1) == " "
    if not items:
        raise Refusal(f"found no checkbox items under Acceptance Criteria or Definition of Done in {path}")
    return unticked


# --- predicates ------------------------------------------------------------

def git_status(repo):
    r = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True)
    if r.returncode:
        raise Refusal(f"git status failed: {r.stderr.strip()}")
    return r.stdout.strip()


def chain_ignored(repo, init):
    """True when the chain documents are untracked and git-ignored (galileo's
    .git/info/exclude keeps docs/ out), so there is no doc-only commit to make."""
    r = subprocess.run(["git", "-C", repo, "check-ignore", "-q", os.path.join(init, "PLAN.org")],
                       capture_output=True, text=True)
    if r.returncode not in (0, 1):
        raise Refusal(f"git check-ignore failed: {r.stderr.strip()}")
    return r.returncode == 0


def tracked_ignored(repo):
    """Tracked paths that match an ignore rule; a new one after a commit stage was force-added."""
    r = subprocess.run(["git", "-C", repo, "ls-files", "-ci", "--exclude-standard"], capture_output=True, text=True)
    if r.returncode:
        raise Refusal(f"git ls-files failed: {r.stderr.strip()}")
    return set(r.stdout.split("\n")) - {""}


def commit_prompt(repo, init):
    if not chain_ignored(repo, init):
        return PROMPTS["commit"]
    return (f"{PROMPTS['commit']} — this repo git-ignores the chain documents under {init}/, so make only the code commit "
            f"and leave them uncommitted; never force-add an ignored path")


def plan_status(repo, init, story):
    for b in batches(read(os.path.join(repo, init, "PLAN.org"))):
        for s in b.stories:
            if s.rel(init) == story.path:
                return s.status
    raise Refusal(f"{story.path} is no longer in PLAN.org")


def predicate(stage, repo, init, story):
    """True when the stage's artifact says it is done. implement has none of its
    own: it runs while the story has an open item, so it shares closeout's."""
    if stage in ("implement", "closeout"):
        return open_items(os.path.join(repo, story.path)) == 0
    if stage == "update-design":
        return plan_status(repo, init, story) == "DONE"
    return git_status(repo) == ""


def describe(stage, repo, init, story):
    if stage in ("implement", "closeout"):
        n = open_items(os.path.join(repo, story.path))
        return f"{n} open item(s) under Acceptance Criteria / Definition of Done"
    if stage == "update-design":
        return f"PLAN heading reads {plan_status(repo, init, story)}"
    return "working tree " + ("clean" if git_status(repo) == "" else "dirty")


def first_stage(repo, init, story):
    for stage in STAGES:
        if not predicate(stage, repo, init, story):
            return stage
    return None


# --- the human's environment -----------------------------------------------

def permission_mode(repo):
    """(mode, source) from the settings the human's interactive sessions use."""
    for path in (os.path.join(repo, ".claude", "settings.local.json"),
                 os.path.join(repo, ".claude", "settings.json"),
                 os.path.expanduser("~/.claude/settings.json")):
        try:
            mode = (json.loads(read(path)).get("permissions") or {}).get("defaultMode")
        except (OSError, ValueError):
            continue
        if mode:
            return mode, path
    return None, None


TIDEWAVE_URL = re.compile(r"https?://\S*/tidewave/mcp\S*")


def tidewave(repo):
    """(name, url) of the repo's Tidewave registration, as the preflight hook finds it:
    local scope in ~/.claude.json first, since Claude Code lets it shadow .mcp.json,
    then .mcp.json. The URL is the server's url, or one in a stdio proxy's command
    line; a proxy naming tidewave with no URL anywhere (mix tidewave.proxy) is
    (name, None), registered but not probeable."""
    def pick(servers):
        for name, s in (servers or {}).items():
            s = s or {}
            argv = [str(a) for a in [s.get("url") or "", s.get("command") or ""] + list(s.get("args") or [])]
            for a in argv:
                m = TIDEWAVE_URL.search(a)
                if m:
                    return name, m.group(0)
            if s.get("type", "stdio") == "stdio" and any("tidewave" in a for a in argv):
                return name, None
        return None
    try:
        projects = json.loads(read(os.path.expanduser("~/.claude.json"))).get("projects") or {}
    except (OSError, ValueError):
        projects = {}
    for key in (repo, os.path.realpath(repo)):
        hit = pick((projects.get(key) or {}).get("mcpServers"))
        if hit:
            return hit
    try:
        return pick(json.loads(read(os.path.join(repo, ".mcp.json"))).get("mcpServers"))
    except (OSError, ValueError):
        return None


def probe(url):
    """None when something answers, else the reason nothing did."""
    req = urllib.request.Request(url, data=b'{"jsonrpc":"2.0","id":1,"method":"ping"}', headers={
        "Content-Type": "application/json", "Accept": "application/json, text/event-stream"})
    try:
        urllib.request.urlopen(req, timeout=2).close()
    except urllib.error.HTTPError:
        return None  # it answered; the preflight hook reports a wrong status itself
    except (urllib.error.URLError, OSError) as e:
        return str(getattr(e, "reason", e))
    return None


# --- Claude ----------------------------------------------------------------

def invoke(argv, cwd, timeout=None):
    """The one place Claude is run. Tests replace this. Returns (rc, stdout, stderr);
    raises StageTimeout after killing the session's whole process group."""
    p = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(p.pid, sig)
                p.communicate(timeout=10)
                break
            except ProcessLookupError:
                break
            except subprocess.TimeoutExpired:
                continue
        raise StageTimeout()
    return p.returncode, out, err


def claude(prompt, repo, mode, session, resume, timeout, flags=()):
    """One turn. The first stage of a story names its session up front
    (--session-id) so even a turn that never returns can be resumed by id.
    flags are the human's own claude options (--plugin-dir), sent every turn."""
    argv = CLAUDE + list(flags) + ["-p", prompt, "--output-format", "json", "--append-system-prompt", SYSTEM_PROMPT]
    if mode:
        argv += ["--permission-mode", mode]
    argv += ["--resume" if resume else "--session-id", session]
    rc, out, err = invoke(argv, repo, timeout=timeout)
    try:
        data = json.loads(out)
    except ValueError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    data.setdefault("result", (out or err or f"claude exited {rc} with no output").strip())
    data["_rc"] = rc
    return data


def result_line(text):
    lines = [l.strip() for l in (text or "").splitlines() if l.strip()]
    return lines[-1] if lines else ""


def lost(data):
    return LOST_RE.match((data.get("result") or "").strip()) is not None


def clean(data):
    return (data["_rc"] == 0 and not data.get("is_error") and data.get("subtype", "success") == "success"
            and result_line(data.get("result")) == DONE_LINE)


# --- the run ---------------------------------------------------------------

def stop(stage, story, session, flags, message, why):
    print(f"\nSTOP at {stage} for {story.name}: {why}", file=sys.stderr)
    print(f"session: {session or '(none started)'}", file=sys.stderr)
    print("final message:\n" + (message or "(none)").rstrip(), file=sys.stderr)
    if session:
        print(f"\nResume with: {' '.join(shlex.quote(a) for a in ['claude', *flags])} --resume {session}\nanswer there, then rerun run-batch.py.", file=sys.stderr)
    return 1


def dirty_message(story, dirty):
    return (f"working tree is not clean before {story.name}'s implement stage, and the driver does not classify or commit what it finds:\n{dirty}\n"
            f"If a stop during implement, or a closeout left with an unticked item, left these changes: finish closeout in the resumed session "
            f"(claude --resume <id>) until every Acceptance Criteria and Definition of Done item in {story.name} is ticked or ruled, then rerun run-batch.py. "
            f"Otherwise commit or stash them yourself, then rerun run-batch.py.")


def run_story(repo, init, story, mode, timeout_min=STAGE_TIMEOUT_MIN, flags=()):
    start = first_stage(repo, init, story)
    if start is None:
        raise Refusal(f"{story.name} reads TODO in PLAN.org but every stage predicate is already true")
    if start == "implement":
        dirty = git_status(repo)
        if dirty:
            raise Refusal(dirty_message(story, dirty))
    session, started = str(uuid.uuid4()), False
    try:
        for stage in STAGES[STAGES.index(start):]:
            if stage != "implement" and predicate(stage, repo, init, story):
                print(f"  {stage}: already done, skipped")
                continue
            if stage == "implement":
                prompt = f"implement @{story.path}"
            elif stage == "commit":
                prompt = commit_prompt(repo, init)
                ignored_before = tracked_ignored(repo)
            else:
                prompt = PROMPTS[stage]
            print(f"  {stage}: {prompt}", flush=True)
            try:
                data = claude(prompt, repo, mode, session, started, timeout_min * 60, flags)
                started = True
                session = data.get("session_id") or session
                if lost(data):
                    print(f"  {stage}: connection lost, sending {CONTINUE} once", flush=True)
                    data = claude(CONTINUE, repo, mode, session, True, timeout_min * 60, flags)
                    session = data.get("session_id") or session
            except StageTimeout:
                return stop(stage, story, session, flags, None,
                            f"no result after {timeout_min:g} min, so the stage was stopped; a step waiting on a permission prompt looks like this")
            if not clean(data):
                return stop(stage, story, session, flags, data.get("result"), "the turn did not end in a clean " + DONE_LINE)
            if stage != "implement" and not predicate(stage, repo, init, story):
                return stop(stage, story, session, flags, data.get("result"),
                            f"the turn said done but its artifact disagrees ({describe(stage, repo, init, story)})")
            if stage == "commit":
                forced = sorted(tracked_ignored(repo) - ignored_before)
                if forced:
                    return stop(stage, story, session, flags, data.get("result"),
                                "the turn committed git-ignored path(s) this repo keeps out of its history: " + ", ".join(forced)
                                + ". Undo that commit's additions by hand (git rm --cached, then amend or a new commit) before rerunning.")
    except Refusal as e:
        # a git read failing mid-story: stop with the session, not a bare refusal
        if not started:
            raise
        return stop(stage, story, session, flags, None, str(e))
    return 0


def preflight(repo):
    """Environment checks before any story. Returns (mode, problems)."""
    problems = []
    mode, source = permission_mode(repo)
    print(f"permission mode: {mode or '(none set; claude default)'}" + (f" (from {source})" if source else ""))
    if mode == "bypassPermissions":
        problems.append("the interactive default permission mode is bypassPermissions; the driver never runs with permission checks bypassed")
    tw = tidewave(repo)
    if tw and not tw[1]:
        print(f"dev server: {tw[0]} is a stdio proxy with no URL in its config; not probed")
    elif tw:
        name, url = tw
        why = probe(url)
        print(f"dev server: {url} " + ("answering" if not why else f"not answering ({why})"))
        if why:
            problems.append(f"Tidewave: nothing is listening at {url} — start this project's dev server, then reconnect {name} in /mcp.")
    else:
        print("dev server: no Tidewave registration; not probed")
    return mode, problems


def dry_run(repo, init, batch, problems):
    stories = batch.todo(init)
    print(f"working tree: {'clean' if git_status(repo) == '' else 'dirty'} (now)")
    print("chain documents: " + ("git-ignored, so the commit stage asks for the code commit only" if chain_ignored(repo, init)
                                 else "tracked, so the commit stage asks for a code commit and a doc-only commit"))
    first = None
    for story in stories:
        print(f"\n{story.name}  ({story.path})")
        start = first_stage(repo, init, story)
        for stage in STAGES:
            if stage == "implement":
                act = "run" if start == "implement" else "skip"
                why = "the story has an open item" if act == "run" else "every item already ticked"
            elif stage == "commit":
                act, why = "check", f"after update-design ({describe(stage, repo, init, story)} now)"
            else:
                act = "skip" if predicate(stage, repo, init, story) else "run"
                why = describe(stage, repo, init, story)
            print(f"  {stage:<14}{act:<6}{why}")
        first = first or (start, story)
    if not first:
        print(f"\nNo TODO story left in {batch.title}: phase-close is next.")
        return 0 if not problems else 1
    start, story = first
    print(f"\nfirst stage: {start} ({os.path.splitext(story.name)[0]})")
    if start == "implement" and git_status(repo):
        problems.append(dirty_message(story, git_status(repo)))
    for p in problems:
        print(f"would refuse: {p}", file=sys.stderr)
    return 1 if problems else 0


def plugin_flags(paths):
    """claude --plugin-dir options for each path, absolute because every turn runs
    from the repo root; a path that is neither a directory nor a .zip is refused."""
    flags = []
    for p in paths:
        full = os.path.realpath(os.path.expanduser(p))
        if not (os.path.isdir(full) or (os.path.isfile(full) and full.endswith(".zip"))):
            raise Refusal(f"--plugin-dir {p}: no such directory or .zip")
        flags += ["--plugin-dir", full]
    return flags


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.getcwd())
    ap.add_argument("--stage-timeout", type=float, default=STAGE_TIMEOUT_MIN, metavar="MINUTES",
                    help=f"wall-clock limit for one stage before the run stops (default {STAGE_TIMEOUT_MIN:g})")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the stories, stages and predicate results it would act on, without invoking Claude")
    ap.add_argument("--plugin-dir", action="append", default=[], metavar="PATH",
                    help="passed to every claude turn and the resume line, as claude --plugin-dir; repeatable")
    args = ap.parse_args(argv)
    repo = os.path.abspath(args.repo)
    try:
        flags = plugin_flags(args.plugin_dir)
        init = active_initiative(repo)
        batch = open_batch(read(os.path.join(repo, init, "PLAN.org")))
        print(f"initiative: {init}/\nopen batch: {batch.title}")
        if args.plugin_dir:
            print("plugin dirs: " + " ".join(flags[1::2]))
        mode, problems = preflight(repo)
        if args.dry_run:
            return dry_run(repo, init, batch, problems)
        if problems:
            raise Refusal("\n".join(problems))
        while True:
            todo = open_batch(read(os.path.join(repo, init, "PLAN.org"))).todo(init)
            if not todo:
                print(f"\nNo TODO story left in {batch.title}: phase-close is next, and it is the human's to run.")
                return 0
            print(f"\n{todo[0].name}", flush=True)
            if run_story(repo, init, todo[0], mode, args.stage_timeout, flags):
                return 1
    except Refusal as e:
        print(f"run-batch: refusing: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
