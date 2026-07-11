#!/bin/bash
# post-edit-format: PostToolUse hook. Guarantees mix format on every edited
# Elixir file — CLAUDE.md asks, hooks enforce.

INPUT=$(cat)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

case "$FILE" in
  *.ex|*.exs)
    # Only inside a Mix project; format just the touched file to stay fast.
    if [ -f "$CLAUDE_PROJECT_DIR/mix.exs" ]; then
      cd "$CLAUDE_PROJECT_DIR" && mix format "$FILE" >/dev/null 2>&1
    fi
    ;;
esac

exit 0
