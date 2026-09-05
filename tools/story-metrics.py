#!/usr/bin/env python3
"""story-metrics — per-story session metrics from Claude Code transcripts.

Reads the JSONL session transcripts Claude Code keeps under
~/.claude/projects/, keeps the sessions whose recorded working directory is
this repo, attributes each to the story its prompts and tool calls name, and
prints an org table (one row per story, a totals row) followed by a per-story
event timeline for the phase-close session to write observations from.

Usage:
  story-metrics.py [--repo PATH] [--projects-dir DIR] [--no-git] STORY...

STORY is a story file path or basename (story-03-archive-replaces-delete.org)
or the bare story-NN key. Attribution is heuristic: a session belongs to the
story named in its user prompts (first one wins); a session whose prompts name
no story falls back to the first story its tool calls reference, but only if it
ran an implementation skill (TDD or story-closeout) — a user-stories run or a
design-time update-design pass that touches every story file is attributed to
none of them. Sessions that touch
several stories are flagged in the Note column.
Python 3 standard library only.
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from collections import defaultdict

IDLE_GAP = 600  # seconds; gaps longer than this are not active time
TEST_RE = re.compile(r"\bmix (test|precommit|check)\b")
STORY_RE = re.compile(r"stories/(story-(\d+)-[a-z][\w.-]*)")
PHASE_SKILLS = {
    "superpowers:test-driven-development": "implement",
    "workflow-kit:story-closeout": "closeout",
    "story-closeout": "closeout",
    "workflow-kit:update-design": "update-design",
    "update-design": "update-design",
}
PHASES = ("implement", "closeout", "update-design")


def parse_ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def same_repo(a, b):
    a, b = os.path.realpath(a), os.path.realpath(b)
    return a == b or a.lower() == b.lower()


def session_cwd(path):
    with open(path) as f:
        for _ in range(20):
            line = f.readline()
            if not line:
                break
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("cwd"):
                return e["cwd"]
    return None


def load_session(path):
    events = []
    with open(path) as f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("timestamp"):
                # every timestamped entry counts toward activity gaps; only
                # user/assistant entries carry content the analysis reads
                e["_t"] = parse_ts(e["timestamp"])
                e.setdefault("type", "other")
                events.append(e)
    return events


def story_key(name):
    m = re.search(r"story-(\d+)", os.path.basename(name))
    return f"story-{m.group(1)}" if m else name


def stories_in(e):
    """(prompt_refs, tool_refs) story keys named by this event."""
    m = e.get("message") or {}
    prompt, tool = [], []
    if e["type"] == "user" and isinstance(m.get("content"), str) and not m["content"].startswith("<"):
        prompt = [f"story-{n}" for _, n in STORY_RE.findall(m["content"])]
    if e["type"] == "assistant":
        for c in m.get("content") or []:
            if isinstance(c, dict) and c.get("type") == "tool_use":
                tool += [f"story-{n}" for _, n in STORY_RE.findall(json.dumps(c.get("input", {})))]
    return prompt, tool


SLASH_RE = re.compile(r"Base directory for this skill: \S*/skills/([\w-]+)")
CMD_RE = re.compile(r"<command-name>/(?:[\w-]+:)?([\w-]+)</command-name>")


def slash_skill(e):
    """Skill name when the user invoked a skill directly, else None."""
    m = e.get("message") or {}
    if e["type"] != "user":
        return None
    c = m.get("content")
    if isinstance(c, list):
        for blk in c:
            if isinstance(blk, dict) and blk.get("type") == "text":
                hit = SLASH_RE.match(blk.get("text", ""))
                if hit:
                    return hit.group(1)
    elif isinstance(c, str):
        hit = CMD_RE.search(c)
        if hit:
            return hit.group(1)
    return None


def phase_of(skill):
    return PHASE_SKILLS.get(skill) or PHASE_SKILLS.get((skill or "").split(":")[-1])


def tool_uses(e):
    m = e.get("message") or {}
    if e["type"] != "assistant":
        return
    for c in m.get("content") or []:
        if isinstance(c, dict) and c.get("type") == "tool_use":
            yield c


def analyse(events, key):
    """Return metrics and timeline for one story from its (sorted) events."""
    phase = "implement"
    starts = {}
    active = defaultdict(float)
    out_tokens = 0
    tests = 0
    verifier = {"count": 0, "ms": 0}
    pending = {}  # tool_use id -> description, for notifications
    timeline = []
    prev_t = None
    for e in events:
        t = e["_t"]
        m = e.get("message") or {}
        sk = slash_skill(e)
        if sk:
            p = phase_of(sk)
            if p and p not in starts:
                phase = p
                starts[p] = t
            # the skill text also follows a model-invoked Skill call, and a
            # slash command yields both a <command-name> marker and the text:
            # record one timeline entry per skill per two minutes
            recent = [l for tt, l in timeline if l.startswith("skill ") and sk in l and (t - tt).total_seconds() < 120]
            if not recent:
                timeline.append((t, f"skill {sk} (slash)"))
        for tu in tool_uses(e):
            name, inp = tu["name"], tu.get("input", {})
            if name == "Skill":
                p = phase_of(inp.get("skill"))
                if p and p not in starts:
                    phase = p
                    starts[p] = t
                    timeline.append((t, f"skill {inp.get('skill')}"))
            elif name == "Agent":
                desc = inp.get("description") or ""
                st = inp.get("subagent_type") or ""
                pending[tu["id"]] = desc
                if "verifier" in st or "verif" in desc.lower():
                    verifier["count"] += 1
                timeline.append((t, f"agent {st}: {desc}"))
            elif name == "AskUserQuestion":
                q = (inp.get("questions") or [{}])[0].get("question", "")
                timeline.append((t, f"question: {q[:100]}"))
            elif name == "Bash":
                cmd = inp.get("command", "")
                if TEST_RE.search(cmd):
                    tests += 1
                if "git commit" in cmd:
                    timeline.append((t, "commit"))
        if e["type"] == "assistant":
            out_tokens += (m.get("usage") or {}).get("output_tokens", 0) or 0
        if e["type"] == "user" and isinstance(m.get("content"), str) and not e.get("isMeta"):
            c = m["content"]
            if c.startswith("<task-notification>"):
                tid = re.search(r"<tool-use-id>([^<]+)", c)
                d = re.search(r"<duration_ms>(\d+)", c)
                desc = pending.get(tid.group(1) if tid else "", "subagent")
                if d:
                    ms = int(d.group(1))
                    if "verif" in desc.lower():
                        verifier["ms"] += ms
                    timeline.append((t, f"done ({ms/60000:.1f} min): {desc}"))
            elif not c.startswith("<"):
                timeline.append((t, f"user: {c[:90]!r}"))
        if prev_t is not None:
            gap = (t - prev_t).total_seconds()
            if 0 <= gap < IDLE_GAP:
                active[phase] += gap
        prev_t = t
    return {
        "active": {p: active[p] / 60 for p in PHASES},
        "tests": tests,
        "verifier": verifier,
        "out_tokens": out_tokens,
        "timeline": timeline,
        "window": (events[0]["_t"], events[-1]["_t"]) if events else None,
    }


def git_delta(repo, windows):
    """(code, test) net line deltas for commits authored inside the session windows."""
    code = test = 0
    seen = set()
    for a, b in windows:
        try:
            out = subprocess.run(
                ["git", "-C", repo, "log", "--format=%H", f"--since={a.isoformat()}", f"--until={b.isoformat()}"],
                capture_output=True, text=True, check=True).stdout.split()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
        for h in out:
            if h in seen:
                continue
            seen.add(h)
            ns = subprocess.run(["git", "-C", repo, "show", "--numstat", "--format=", h],
                                capture_output=True, text=True).stdout
            for line in ns.splitlines():
                parts = line.split("\t")
                if len(parts) != 3 or parts[0] == "-":
                    continue
                add, rm, path = int(parts[0]), int(parts[1]), parts[2]
                if path.startswith("docs/"):
                    continue
                if path.startswith("test/") or "_test." in path:
                    test += add - rm
                else:
                    code += add - rm
    return code, test


def fmt_k(n):
    return f"{n/1000:.1f}k"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stories", nargs="+")
    ap.add_argument("--repo", default=os.getcwd())
    ap.add_argument("--projects-dir", default=os.path.expanduser("~/.claude/projects"))
    ap.add_argument("--no-git", action="store_true", help="skip commit line deltas")
    ap.add_argument("--list-sessions", action="store_true", help="print session -> story attribution and exit")
    args = ap.parse_args()

    keys = [story_key(s) for s in args.stories]
    sessions = []
    for d in sorted(os.listdir(args.projects_dir)) if os.path.isdir(args.projects_dir) else []:
        dd = os.path.join(args.projects_dir, d)
        if not os.path.isdir(dd):
            continue
        for fn in sorted(os.listdir(dd)):
            if not fn.endswith(".jsonl"):
                continue
            path = os.path.join(dd, fn)
            cwd = session_cwd(path)
            if cwd and same_repo(cwd, args.repo):
                sessions.append(path)

    by_story = defaultdict(list)   # key -> events
    flagged = defaultdict(set)     # key -> other stories seen in the same session
    orphan_updates = []            # (start, events) of update-design-only sessions
    for path in sessions:
        events = load_session(path)
        prompt_refs, tool_refs = [], []
        phases_run = set()
        for e in events:
            pr, tr = stories_in(e)
            prompt_refs += [k for k in pr if k not in prompt_refs]
            tool_refs += [k for k in tr if k not in tool_refs]
            sk = slash_skill(e)
            if sk and phase_of(sk):
                phases_run.add(phase_of(sk))
            for tu in tool_uses(e):
                if tu["name"] == "Skill" and phase_of(tu.get("input", {}).get("skill")):
                    phases_run.add(phase_of(tu.get("input", {}).get("skill")))
        anchored = bool(phases_run & {"implement", "closeout"})
        refs = prompt_refs or (tool_refs if anchored else [])
        if not refs:
            if "update-design" in phases_run:
                # standalone update-design pass: scope is the most recently
                # closed-out story, per the skill's own definition
                orphan_updates.append((events[0]["_t"], events))
            continue
        owner = refs[0]
        if args.list_sessions:
            print(f"{os.path.basename(path)[:8]}  {events[0]['_t']:%m-%d %H:%M}→{events[-1]['_t']:%H:%M}  {len(events):5} events  owner {owner}  prompts {prompt_refs}  tools {tool_refs[:6]}")
        by_story[owner].extend(events)
        for other in prompt_refs[1:] + tool_refs:
            if other != owner:
                flagged[owner].add(other)

    closeouts = {}  # key -> time of the latest closeout invocation
    for k, evs in by_story.items():
        for e in evs:
            sk = slash_skill(e)
            names = [sk] if sk else [tu.get("input", {}).get("skill") for tu in tool_uses(e) if tu["name"] == "Skill"]
            if any(phase_of(n) == "closeout" for n in names):
                closeouts[k] = max(closeouts.get(k, e["_t"]), e["_t"])
    for start, evs in orphan_updates:
        prior = [(t, k) for k, t in closeouts.items() if t <= start]
        if prior:
            k = max(prior)[1]
            by_story[k].extend(evs)
            if args.list_sessions:
                print(f"{'':8}  standalone update-design {start:%m-%d %H:%M} attributed to {k} (most recent close-out)")
    if args.list_sessions:
        return 0
    rows = []
    totals = defaultdict(float)
    timelines = {}
    for k in keys:
        events = sorted(by_story.get(k, []), key=lambda e: e["_t"])
        if not events:
            rows.append(f"| {k} | - | - | - | - | - | - | - | - | no transcript on this machine |")
            continue
        r = analyse(events, k)
        delta = None if args.no_git else git_delta(args.repo, [r["window"]])
        code, test = (delta if delta else ("-", "-"))
        v = r["verifier"]
        note = f"also read {', '.join(sorted(flagged[k]))}" if flagged.get(k) else ""
        rows.append(
            f"| {k} | {r['active']['implement']:.0f} | {r['active']['closeout']:.0f} | {r['active']['update-design']:.0f}"
            f" | {r['tests']} | {v['count']}({v['ms']/60000:.1f}m) | {fmt_k(r['out_tokens'])} | {code} | {test} | {note} |")
        for p in PHASES:
            totals[p] += r["active"][p]
        totals["tests"] += r["tests"]
        totals["vcount"] += v["count"]
        totals["vms"] += v["ms"]
        totals["tok"] += r["out_tokens"]
        if delta:
            totals["code"] += code
            totals["test"] += test
        timelines[k] = r["timeline"]

    print("| Story | Impl min | Closeout min | Update-design min | Test runs | Verifier | Out tokens | Δcode | Δtest | Note |")
    print("|-------+----------+--------------+-------------------+-----------+----------+------------+-------+-------+------|")
    for row in rows:
        print(row)
    print(f"| total | {totals['implement']:.0f} | {totals['closeout']:.0f} | {totals['update-design']:.0f} | {totals['tests']:.0f}"
          f" | {totals['vcount']:.0f}({totals['vms']/60000:.1f}m) | {fmt_k(totals['tok'])}"
          f" | {'-' if args.no_git else int(totals['code'])} | {'-' if args.no_git else int(totals['test'])} | |")
    print()
    print("Minutes are active time (idle gaps over 10 min excluded). Verifier is dispatch count (total minutes). Δ is net lines in commits inside the session window, docs/ excluded. Note lists other story files the sessions referenced — reads count, so it is not evidence of edits.")
    print()
    print("Timeline (for writing observations — not for pasting into retro.org):")
    for k in keys:
        if k not in timelines:
            continue
        print(f"\n{k}")
        for t, line in timelines[k]:
            print(f"  {t:%m-%d %H:%M}  {line}")


if __name__ == "__main__":
    sys.exit(main())
