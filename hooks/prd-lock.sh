#!/bin/bash
# prd-lock: PreToolUse hook. PRD.org is the invariant contract — human-only edits
# via the Amendment protocol. Exit 2 blocks the tool call; stderr is fed to Claude.

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty')

BLOCK_MSG="BLOCKED by prd-lock: PRD.org is the invariant contract and is never edited by agents. If implementation conflicts with the Success Criteria, stop and surface it to the human — that is an Amendment decision (see the protocol in PRD.org). Design pivots belong in DESIGN.org with a Changelog entry."

case "$TOOL" in
  Edit|Write|MultiEdit|NotebookEdit)
    FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
    case "$FILE" in
      *PRD.org)
        echo "$BLOCK_MSG" >&2
        exit 2
        ;;
    esac
    ;;
  Bash)
    CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
    if echo "$CMD" | grep -q 'PRD\.org'; then
      # Allow read-only access; block write-shaped commands targeting PRD.org.
      if echo "$CMD" | grep -qE '(>|>>)[[:space:]]*[^[:space:]]*PRD\.org|sed[[:space:]].*-i[^[:space:]]*[[:space:]].*PRD\.org|tee[[:space:]].*PRD\.org|(mv|cp)[[:space:]].*[[:space:]][^[:space:]]*PRD\.org|rm[[:space:]].*PRD\.org|truncate[[:space:]].*PRD\.org'; then
        echo "$BLOCK_MSG" >&2
        exit 2
      fi
    fi
    ;;
esac

exit 0
