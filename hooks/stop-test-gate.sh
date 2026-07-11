#!/bin/bash
# stop-test-gate: OPTIONAL Stop hook, not wired into settings.json by default.
# When enabled, Claude cannot end a turn while mix test is failing — exit 2
# feeds the failures back and forces it to keep working. Enable for work-grade
# repos where a red suite should never be left standing; leave off for MVP
# weight class where the story-closeout verifier already runs the suite.
#
# To enable, add to .claude/settings.json under "hooks":
#   "Stop": [ { "hooks": [ { "type": "command",
#     "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/stop-test-gate.sh\"" } ] } ]

INPUT=$(cat)

# Prevent infinite loops: if a Stop hook already forced continuation once,
# allow stopping on subsequent invocations.
ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')
if [ "$ACTIVE" = "true" ]; then
  exit 0
fi

# Only meaningful inside a Mix project.
if [ ! -f "$CLAUDE_PROJECT_DIR/mix.exs" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR" || exit 0
OUTPUT=$(mix test 2>&1)
if [ $? -ne 0 ]; then
  echo "stop-test-gate: mix test is failing. Fix the suite before stopping." >&2
  echo "$OUTPUT" | tail -30 >&2
  exit 2
fi

exit 0
