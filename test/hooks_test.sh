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

echo "== prd-lock: bash reads allowed =="
check "cat"           "$(hook_exit prd-lock.sh '{"tool_name":"Bash","tool_input":{"command":"cat PRD.org"}}')" 0
check "grep"          "$(hook_exit prd-lock.sh '{"tool_name":"Bash","tool_input":{"command":"grep -n Success PRD.org"}}')" 0
check "unrelated cmd" "$(hook_exit prd-lock.sh '{"tool_name":"Bash","tool_input":{"command":"mix test"}}')" 0

echo "== post-edit-format =="
check "no mix.exs no-op" "$(echo '{"tool_name":"Edit","tool_input":{"file_path":"lib/foo.ex"}}' | CLAUDE_PROJECT_DIR=/tmp "$ROOT/hooks/post-edit-format.sh" >/dev/null 2>&1; echo $?)" 0
check "non-elixir no-op" "$(echo '{"tool_name":"Edit","tool_input":{"file_path":"README.md"}}' | CLAUDE_PROJECT_DIR=/tmp "$ROOT/hooks/post-edit-format.sh" >/dev/null 2>&1; echo $?)" 0

echo "== stop-test-gate =="
check "stop_hook_active passthrough" "$(echo '{"stop_hook_active":true}' | CLAUDE_PROJECT_DIR=/tmp "$ROOT/hooks/stop-test-gate.sh" >/dev/null 2>&1; echo $?)" 0
check "no mix.exs no-op"             "$(echo '{"stop_hook_active":false}' | CLAUDE_PROJECT_DIR=/tmp "$ROOT/hooks/stop-test-gate.sh" >/dev/null 2>&1; echo $?)" 0

echo "== skill/agent frontmatter lint =="
for f in "$ROOT"/skills/*/SKILL.md "$ROOT"/agents/*.md; do
  rel="${f#"$ROOT"/}"
  if head -1 "$f" | grep -q '^---$' && grep -q '^name:' "$f" && grep -q '^description:' "$f"; then
    check "frontmatter $rel" 0 0
  else
    check "frontmatter $rel" 1 0
  fi
done

echo "== no 'Changelog' stragglers in skills/templates/project-setup =="
strays="$(grep -rl -e Changelog -e changelog "$ROOT/skills" "$ROOT/templates" "$ROOT/project-setup" 2>/dev/null | wc -l | tr -d ' ')"
check "no Changelog/changelog strings" "$strays" 0

echo "== no '%Z' timestamp stragglers in skills/templates =="
strays="$(grep -rl -- '%Z' "$ROOT/skills" "$ROOT/templates" 2>/dev/null | wc -l | tr -d ' ')"
check "no %Z strings" "$strays" 0

echo
echo "passed: $PASS  failed: $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
