#!/usr/bin/env bash
# hooks_test.sh — behavioral tests for workflow-kit hooks plus manifest/frontmatter lint.
# Run from anywhere; exits nonzero on any failure. Requires: bash, jq.

set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PASS=0
FAIL=0

check() { # check <description> <actual> <expected>
  if [ "$2" = "$3" ]; then
    PASS=$((PASS + 1))
    echo "  ok: $1"
  else
    FAIL=$((FAIL + 1))
    echo "  FAIL: $1 (got $2, want $3)"
  fi
}

hook_exit() { # hook_exit <script> <json>
  echo "$2" | "$ROOT/hooks/$1" >/dev/null 2>&1
  echo $?
}

echo "== prerequisites =="
command -v jq >/dev/null || { echo "FAIL: jq not on PATH"; exit 1; }
echo "  ok: jq present"

echo "== shell syntax =="
for s in "$ROOT"/hooks/*.sh; do
  if bash -n "$s"; then check "syntax $(basename "$s")" 0 0; else check "syntax $(basename "$s")" 1 0; fi
done

echo "== JSON validity =="
for j in "$ROOT/hooks/hooks.json" "$ROOT/.claude-plugin/plugin.json" "$ROOT/.claude-plugin/marketplace.json" "$ROOT/project-setup/copy-in-settings.json"; do
  if jq empty "$j" 2>/dev/null; then check "valid JSON $(basename "$j")" 0 0; else check "valid JSON $(basename "$j")" 1 0; fi
done

echo "== prd-lock: file tools =="
check "Edit PRD.org blocked"        "$(hook_exit prd-lock.sh '{"tool_name":"Edit","tool_input":{"file_path":"/repo/PRD.org"}}')" 2
check "Write PRD.org blocked"       "$(hook_exit prd-lock.sh '{"tool_name":"Write","tool_input":{"file_path":"PRD.org"}}')" 2
check "MultiEdit PRD.org blocked"   "$(hook_exit prd-lock.sh '{"tool_name":"MultiEdit","tool_input":{"file_path":"docs/PRD.org"}}')" 2
check "Edit DESIGN.org allowed"     "$(hook_exit prd-lock.sh '{"tool_name":"Edit","tool_input":{"file_path":"/repo/DESIGN.org"}}')" 0
check "Edit story allowed"          "$(hook_exit prd-lock.sh '{"tool_name":"Edit","tool_input":{"file_path":"stories/story-01-setup.org"}}')" 0

echo "== prd-lock: bash write-shapes blocked =="
check "redirect >"    "$(hook_exit prd-lock.sh '{"tool_name":"Bash","tool_input":{"command":"echo hacked > PRD.org"}}')" 2
check "append >>"     "$(hook_exit prd-lock.sh '{"tool_name":"Bash","tool_input":{"command":"echo more >> PRD.org"}}')" 2
check "sed -i"        "$(hook_exit prd-lock.sh '{"tool_name":"Bash","tool_input":{"command":"sed -i s/a/b/ PRD.org"}}')" 2
check "tee"           "$(hook_exit prd-lock.sh '{"tool_name":"Bash","tool_input":{"command":"cat notes.txt | tee PRD.org"}}')" 2
check "rm"            "$(hook_exit prd-lock.sh '{"tool_name":"Bash","tool_input":{"command":"rm PRD.org"}}')" 2
check "mv onto"       "$(hook_exit prd-lock.sh '{"tool_name":"Bash","tool_input":{"command":"mv draft.org PRD.org"}}')" 2
check "truncate"      "$(hook_exit prd-lock.sh '{"tool_name":"Bash","tool_input":{"command":"truncate -s0 PRD.org"}}')" 2
check "rm by path"    "$(hook_exit prd-lock.sh '{"tool_name":"Bash","tool_input":{"command":"/bin/rm -f docs/x/PRD.org"}}')" 2
check "rm after &&"   "$(hook_exit prd-lock.sh '{"tool_name":"Bash","tool_input":{"command":"cd docs/x && rm PRD.org"}}')" 2

echo "== prd-lock: prose containing a command word is not a command =="
check "\"from PRD.org\" allowed"  "$(hook_exit prd-lock.sh '{"tool_name":"Bash","tool_input":{"command":"echo \"the brainstorm starts from PRD.org and SKETCH.org\""}}')" 0
check "\"used -i PRD.org\" allowed" "$(hook_exit prd-lock.sh '{"tool_name":"Bash","tool_input":{"command":"echo \"notes: I used -i on PRD.org once\""}}')" 0

echo "== prd-lock: bash reads allowed =="
check "cat"           "$(hook_exit prd-lock.sh '{"tool_name":"Bash","tool_input":{"command":"cat PRD.org"}}')" 0
check "grep"          "$(hook_exit prd-lock.sh '{"tool_name":"Bash","tool_input":{"command":"grep -n Success PRD.org"}}')" 0
check "unrelated cmd" "$(hook_exit prd-lock.sh '{"tool_name":"Bash","tool_input":{"command":"mix test"}}')" 0

echo "== prd-lock: PRD-draft.org is unrestricted (create-prd's draft-then-rename flow) =="
check "Edit PRD-draft.org allowed"  "$(hook_exit prd-lock.sh '{"tool_name":"Edit","tool_input":{"file_path":"docs/2026-07-11-x/PRD-draft.org"}}')" 0
check "Write PRD-draft.org allowed" "$(hook_exit prd-lock.sh '{"tool_name":"Write","tool_input":{"file_path":"docs/2026-07-11-x/PRD-draft.org"}}')" 0
check "MultiEdit PRD-draft.org allowed" "$(hook_exit prd-lock.sh '{"tool_name":"MultiEdit","tool_input":{"file_path":"docs/2026-07-11-x/PRD-draft.org"}}')" 0
check "redirect > draft allowed"    "$(hook_exit prd-lock.sh '{"tool_name":"Bash","tool_input":{"command":"echo hi > docs/2026-07-11-x/PRD-draft.org"}}')" 0
check "sed -i draft allowed"        "$(hook_exit prd-lock.sh '{"tool_name":"Bash","tool_input":{"command":"sed -i s/a/b/ docs/2026-07-11-x/PRD-draft.org"}}')" 0
check "tee draft allowed"           "$(hook_exit prd-lock.sh '{"tool_name":"Bash","tool_input":{"command":"cat notes.txt | tee docs/2026-07-11-x/PRD-draft.org"}}')" 0

echo "== prd-lock: rename/copy of a draft onto PRD.org still blocked =="
check "mv draft onto PRD.org blocked" "$(hook_exit prd-lock.sh '{"tool_name":"Bash","tool_input":{"command":"mv docs/2026-07-11-x/PRD-draft.org docs/2026-07-11-x/PRD.org"}}')" 2
check "cp draft onto PRD.org blocked" "$(hook_exit prd-lock.sh '{"tool_name":"Bash","tool_input":{"command":"cp docs/2026-07-11-x/PRD-draft.org docs/2026-07-11-x/PRD.org"}}')" 2

echo "== post-edit-format =="
check "no mix.exs no-op" "$(echo '{"tool_name":"Edit","tool_input":{"file_path":"lib/foo.ex"}}' | CLAUDE_PROJECT_DIR=/tmp "$ROOT/hooks/post-edit-format.sh" >/dev/null 2>&1; echo $?)" 0
check "non-elixir no-op" "$(echo '{"tool_name":"Edit","tool_input":{"file_path":"README.md"}}' | CLAUDE_PROJECT_DIR=/tmp "$ROOT/hooks/post-edit-format.sh" >/dev/null 2>&1; echo $?)" 0

echo "== stop-test-gate =="
check "stop_hook_active passthrough" "$(echo '{"stop_hook_active":true}' | CLAUDE_PROJECT_DIR=/tmp "$ROOT/hooks/stop-test-gate.sh" >/dev/null 2>&1; echo $?)" 0
check "no mix.exs no-op"             "$(echo '{"stop_hook_active":false}' | CLAUDE_PROJECT_DIR=/tmp "$ROOT/hooks/stop-test-gate.sh" >/dev/null 2>&1; echo $?)" 0

echo "== tidewave-preflight =="
TWDIR="$(mktemp -d)"
TWHOME="$(mktemp -d)"
tw_out() { # tw_out <cwd> -> hook stdout
  echo "{\"cwd\":\"$1\",\"hook_event_name\":\"SessionStart\",\"source\":\"startup\"}" \
    | HOME="$TWHOME" "$ROOT/hooks/tidewave-preflight.sh" 2>/dev/null
}
tw_rc() { # tw_rc <cwd> -> exit status
  echo "{\"cwd\":\"$1\"}" | HOME="$TWHOME" "$ROOT/hooks/tidewave-preflight.sh" >/dev/null 2>&1
  echo $?
}
tw_ctx() { # tw_ctx <hook stdout> -> the injected context
  echo "$1" | jq -r '.hookSpecificOutput.additionalContext // empty' 2>/dev/null
}

# Not applicable: no MCP config at all, and a project whose only server is not Tidewave.
check "no MCP config is silent"       "$(tw_out "$TWDIR")" ""
check "no MCP config exits 0"         "$(tw_rc "$TWDIR")" 0
echo '{"mcpServers":{"playwright":{"type":"stdio","command":"npx"}}}' > "$TWDIR/.mcp.json"
check "non-tidewave server is silent" "$(tw_out "$TWDIR")" ""

# Configured but nothing listening: port 1 refuses immediately.
echo '{"mcpServers":{"tidewave":{"type":"http","url":"http://127.0.0.1:1/tidewave/mcp"}}}' > "$TWDIR/.mcp.json"
tw_down="$(tw_out "$TWDIR")"
check "down server warns about dev server" "$(tw_ctx "$tw_down" | grep -c 'dev server')" 1
check "down server names the URL"          "$(tw_ctx "$tw_down" | grep -c '127.0.0.1:1/tidewave/mcp')" 1
check "down server still exits 0"          "$(tw_rc "$TWDIR")" 0

# The URL also resolves from ~/.claude.json, which is where Claude Code keeps it.
rm -f "$TWDIR/.mcp.json"
jq -n --arg d "$TWDIR" '{projects:{($d):{mcpServers:{jump:{type:"http",url:"http://127.0.0.1:1/tidewave/mcp"}}}}}' > "$TWHOME/.claude.json"
check "URL found in ~/.claude.json"        "$(tw_ctx "$(tw_out "$TWDIR")" | grep -c 'dev server')" 1
check "other project's server ignored"     "$(tw_out "$(mktemp -d)")" ""

# Server up: a stub that answers the ping with 200.
TWPORT="$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));p=s.getsockname()[1];s.close();print(p)')"
python3 "$ROOT/test/fixtures/tidewave-stub.py" "$TWPORT" &
TWPID=$!
for _ in 1 2 3 4 5 6 7 8 9 10; do
  curl -s -m 1 -o /dev/null "http://127.0.0.1:$TWPORT/tidewave/mcp" && break
  sleep 0.2
done
jq -n --arg u "http://127.0.0.1:$TWPORT/tidewave/mcp" '{mcpServers:{tidewave:{type:"http",url:$u}}}' > "$TWDIR/.mcp.json"
check "live endpoint is silent"       "$(tw_out "$TWDIR")" ""
check "live endpoint exits 0"         "$(tw_rc "$TWDIR")" 0

# Listening, but that path is not a Tidewave endpoint: wrong app on the port, or wrong transport.
jq -n --arg u "http://127.0.0.1:$TWPORT/wrong/tidewave/mcp" '{mcpServers:{tidewave:{type:"http",url:$u}}}' > "$TWDIR/.mcp.json"
check "non-200 response is reported"  "$(tw_ctx "$(tw_out "$TWDIR")" | grep -c 'HTTP 404')" 1
check "non-200 response exits 0"      "$(tw_rc "$TWDIR")" 0

kill "$TWPID" 2>/dev/null
wait "$TWPID" 2>/dev/null
rm -rf "$TWDIR" "$TWHOME"

echo "== skill/agent frontmatter lint =="
for f in "$ROOT"/skills/*/SKILL.md "$ROOT"/agents/*.md; do
  rel="${f#"$ROOT"/}"
  if head -1 "$f" | grep -q '^---$' && grep -q '^name:' "$f" && grep -q '^description:' "$f"; then
    check "frontmatter $rel" 0 0
  else
    check "frontmatter $rel" 1 0
  fi
done

echo "== model routing pins =="
for pair in \
  "skills/story-closeout/SKILL.md=sonnet" \
  "skills/create-prd/SKILL.md=opus" \
  "skills/promote-design/SKILL.md=opus" \
  "skills/user-stories/SKILL.md=opus" \
  "skills/update-design/SKILL.md=opus" \
  "skills/phase-close/SKILL.md=opus" \
  "agents/story-verifier.md=sonnet" \
  "agents/skeptic-reviewer.md=opus"; do
  rel="${pair%%=*}"; want="${pair##*=}"
  got="$(sed -n '2,/^---$/p' "$ROOT/$rel" | sed -n 's/^model: *//p')"
  check "model pin $rel is $want" "$got" "$want"
done
check "copy-in settings default model is sonnet" "$(jq -r '.model' "$ROOT/project-setup/copy-in-settings.json")" sonnet

echo "== story-metrics script =="
FIX="$ROOT/test/fixtures/story-metrics"
OUT="$(python3 "$ROOT/tools/story-metrics.py" --repo /fixture/repo --projects-dir "$FIX/projects" --no-git story-01-widget 2>/dev/null)"
check "story-metrics exits 0"        "$(python3 "$ROOT/tools/story-metrics.py" --repo /fixture/repo --projects-dir "$FIX/projects" --no-git story-01-widget >/dev/null 2>&1; echo $?)" 0
check "story-metrics row present"    "$(echo "$OUT" | grep -c '^| story-01 ')" 1
check "story-metrics phase minutes"  "$(echo "$OUT" | grep '^| story-01 ' | awk -F'|' '{gsub(/ /,"",$3); gsub(/ /,"",$4); gsub(/ /,"",$5); print $3"/"$4"/"$5}')" "5/3/3"
check "story-metrics test runs"      "$(echo "$OUT" | grep '^| story-01 ' | awk -F'|' '{gsub(/ /,"",$6); print $6}')" 2
check "story-metrics verifier"       "$(echo "$OUT" | grep '^| story-01 ' | awk -F'|' '{gsub(/ /,"",$7); print $7}')" "1(2.0m)"
check "story-metrics output tokens"  "$(echo "$OUT" | grep '^| story-01 ' | awk -F'|' '{gsub(/ /,"",$8); print $8}')" "5.0k"
check "story-metrics ignores other cwd" "$(echo "$OUT" | grep -c '9999\|10.0k')" 0
check "story-metrics timeline has question" "$(echo "$OUT" | grep -c 'Defer AC-3')" 1
check "story-metrics prompt wins over tool refs" "$(python3 "$ROOT/tools/story-metrics.py" --repo /fixture/repo --projects-dir "$FIX/projects" --no-git story-02-gadget 2>/dev/null | grep '^| story-02 ' | awk -F'|' '{gsub(/ /,"",$8); print $8}')" "10.0k"
check "story-metrics story-01 unpolluted" "$(echo "$OUT" | grep '^| story-01 ' | awk -F'|' '{gsub(/ /,"",$8); print $8}')" "5.0k"
check "story-metrics slash-invoked skill in timeline" "$(echo "$OUT" | grep -c 'skill update-design (slash)')" 1
check "story-metrics same number, other initiative, not folded in" "$(echo "$OUT" | grep -c '7.8k\|12.8k')" 0
check "story-metrics other initiative's story-01 stands alone" "$(python3 "$ROOT/tools/story-metrics.py" --repo /fixture/repo --projects-dir "$FIX/projects" --no-git story-01-gizmo.org 2>/dev/null | grep '^| story-01 ' | awk -F'|' '{gsub(/ /,"",$8); print $8}')" "7.8k"
check "story-metrics verifier minutes: background by notification, foreground by tool_result" "$(python3 "$ROOT/tools/story-metrics.py" --repo /fixture/repo --projects-dir "$FIX/projects" --no-git story-01-gizmo.org 2>/dev/null | grep '^| story-01 ' | awk -F'|' '{gsub(/ /,"",$7); print $7}')" "2(7.0m)"
check "story-metrics missing story flagged" "$(python3 "$ROOT/tools/story-metrics.py" --repo /fixture/repo --projects-dir "$FIX/projects" --no-git story-09-none 2>/dev/null | grep -c '^| story-09 .*no transcript')" 1

echo "== no 'Changelog' stragglers in skills/templates/project-setup =="
strays="$(grep -rl -e Changelog -e changelog "$ROOT/skills" "$ROOT/templates" "$ROOT/project-setup" 2>/dev/null | wc -l | tr -d ' ')"
check "no Changelog/changelog strings" "$strays" 0

echo "== no '%Z' timestamp stragglers in skills/templates =="
strays="$(grep -rl -- '%Z' "$ROOT/skills" "$ROOT/templates" 2>/dev/null | wc -l | tr -d ' ')"
check "no %Z strings" "$strays" 0

echo
echo "passed: $PASS  failed: $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
