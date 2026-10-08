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
only for a connection lost mid-response.

It refuses with no open batch, a dirty tree before a story's implement stage,
a Tidewave dev server not answering, or a bypassPermissions default. The
permission mode is the human's interactive default (permissions.defaultMode).

Usage:
  run-batch.py [--repo PATH] [--dry-run]

Design: docs/2026-10-08-batch-driver-design.org in the kit.
Python 3 standard library only.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

STAGES = ("implement", "closeout", "update-design", "commit")
PROMPTS = {
    "closeout": "/workflow-kit:story-closeout",
    "update-design": "/workflow-kit:update-design",
    "commit": "commit",
}
CONTINUE = "continue"
DONE_LINE = "RESULT: done"
LOST_RE = re.compile(r"^API Error: Connection lost", re.I)

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
- commit: a code commit, then a doc-only commit, and a clean working tree. A commit that cannot be signed is blocked; never bypass signing.
- continue: finish the turn the lost connection interrupted, with its expected outcome."""


class Refusal(Exception):
    """A precondition the driver will not work around."""


def read(path):
    with open(path) as f:
        return f.read()


# --- the chain -------------------------------------------------------------

def active_initiative(repo):
    """The initiative directory named by CLAUDE.md's Active initiative: line."""
    path = os.path.join(repo, "CLAUDE.md")
    if not os.path.isfile(path):
        raise Refusal("no CLAUDE.md, so no Active initiative: line to resolve the chain from")
    m = re.search(r"^Active initiative:\s*(\S+)", read(path), re.M)
    if not m or m.group(1).rstrip(".") == "none":
        raise Refusal("CLAUDE.md names no active initiative")
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


def tidewave(repo):
    """(name, url) of the repo's Tidewave registration, as the preflight hook finds it."""
    def pick(servers):
        for name, s in (servers or {}).items():
            url = (s or {}).get("url") or ""
            if "/tidewave/mcp" in url:
                return name, url
        return None
    try:
        hit = pick(json.loads(read(os.path.join(repo, ".mcp.json"))).get("mcpServers"))
        if hit:
            return hit
    except (OSError, ValueError):
        pass
    try:
        projects = json.loads(read(os.path.expanduser("~/.claude.json"))).get("projects") or {}
    except (OSError, ValueError):
        return None
    for key in (repo, os.path.realpath(repo)):
        hit = pick((projects.get(key) or {}).get("mcpServers"))
        if hit:
            return hit
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

def invoke(argv, cwd):
    """The one place Claude is run. Tests replace this. Returns (rc, stdout, stderr)."""
    r = subprocess.run(argv, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def claude(prompt, repo, mode, session):
    argv = ["claude", "-p", prompt, "--output-format", "json", "--append-system-prompt", SYSTEM_PROMPT]
    if mode:
        argv += ["--permission-mode", mode]
    if session:
        argv += ["--resume", session]
    rc, out, err = invoke(argv, repo)
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

def stop(stage, story, session, message, why):
    print(f"\nSTOP at {stage} for {story.name}: {why}", file=sys.stderr)
    print(f"session: {session or '(none started)'}", file=sys.stderr)
    print("final message:\n" + (message or "(none)").rstrip(), file=sys.stderr)
    if session:
        print(f"\nResume with: claude --resume {session}\nanswer there, then rerun run-batch.py.", file=sys.stderr)
    return 1


def dirty_message(story, dirty):
    return (f"working tree is not clean before {story.name}'s implement stage, and the driver does not classify or commit what it finds:\n{dirty}\n"
            f"If a stop during implement, or a closeout left with an unticked item, left these changes: finish closeout in the resumed session "
            f"(claude --resume <id>) until every Acceptance Criteria and Definition of Done item in {story.name} is ticked or ruled, then rerun run-batch.py. "
            f"Otherwise commit or stash them yourself, then rerun run-batch.py.")


def run_story(repo, init, story, mode):
    start = first_stage(repo, init, story)
    if start is None:
        raise Refusal(f"{story.name} reads TODO in PLAN.org but every stage predicate is already true")
    if start == "implement":
        dirty = git_status(repo)
        if dirty:
            raise Refusal(dirty_message(story, dirty))
    session = None
    for stage in STAGES[STAGES.index(start):]:
        if stage != "implement" and predicate(stage, repo, init, story):
            print(f"  {stage}: already done, skipped")
            continue
        prompt = f"implement @{story.path}" if stage == "implement" else PROMPTS[stage]
        print(f"  {stage}: {prompt}", flush=True)
        data = claude(prompt, repo, mode, session)
        session = data.get("session_id") or session
        if lost(data) and session:
            print(f"  {stage}: connection lost, sending {CONTINUE} once", flush=True)
            data = claude(CONTINUE, repo, mode, session)
            session = data.get("session_id") or session
        if not clean(data):
            return stop(stage, story, session, data.get("result"), "the turn did not end in a clean " + DONE_LINE)
        if stage != "implement" and not predicate(stage, repo, init, story):
            return stop(stage, story, session, data.get("result"),
                        f"the turn said done but its artifact disagrees ({describe(stage, repo, init, story)})")
    return 0


def preflight(repo):
    """Environment checks before any story. Returns (mode, problems)."""
    problems = []
    mode, source = permission_mode(repo)
    print(f"permission mode: {mode or '(none set; claude default)'}" + (f" (from {source})" if source else ""))
    if mode == "bypassPermissions":
        problems.append("the interactive default permission mode is bypassPermissions; the driver never runs with permission checks bypassed")
    tw = tidewave(repo)
    if tw:
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


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.getcwd())
    ap.add_argument("--dry-run", action="store_true",
                    help="print the stories, stages and predicate results it would act on, without invoking Claude")
    args = ap.parse_args(argv)
    repo = os.path.abspath(args.repo)
    try:
        init = active_initiative(repo)
        batch = open_batch(read(os.path.join(repo, init, "PLAN.org")))
        print(f"initiative: {init}/\nopen batch: {batch.title}")
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
            if run_story(repo, init, todo[0], mode):
                return 1
    except Refusal as e:
        print(f"run-batch: refusing: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
