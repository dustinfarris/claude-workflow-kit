#!/bin/bash
# tidewave-preflight: SessionStart hook. Tidewave's MCP tools only answer while the
# project's dev server is running, so a session that starts against a stopped server
# discovers the problem at its first mcp__tidewave__* call — after the tokens that got
# it there are already spent. This probes the endpoint once at session start and, when
# it is not answering, warns the human directly (systemMessage) and tells the session to
# raise it in its first reply, so the server gets started before any work begins rather
# than mid-task. Advisory only: it never blocks a tool call and never starts anything
# itself.
#
# No-op unless this project has an MCP server whose URL contains /tidewave/mcp, so it
# stays silent in every non-Tidewave repo the plugin is enabled in.

INPUT=$(cat)

command -v jq >/dev/null 2>&1 || exit 0
command -v curl >/dev/null 2>&1 || exit 0

CWD=$(echo "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)
[ -n "$CWD" ] || CWD="${CLAUDE_PROJECT_DIR:-}"
[ -n "$CWD" ] || exit 0

# The URL Claude Code itself would dial: the project's checked-in config first, then
# the per-project entry in ~/.claude.json, where `claude mcp add` writes it. Matching on
# the URL rather than the server name catches the ones registered under another name.
# Each candidate is "<server name> <url>"; the name is what the human reconnects in /mcp.
ENTRY=""
if [ -f "$CWD/.mcp.json" ]; then
  ENTRY=$(jq -r '(.mcpServers // {}) | to_entries[] | "\(.key) \(.value.url // "")"' "$CWD/.mcp.json" 2>/dev/null \
        | grep -m1 '/tidewave/mcp')
fi
if [ -z "$ENTRY" ] && [ -f "$HOME/.claude.json" ]; then
  ENTRY=$(jq -r --arg d "$CWD" '((.projects[$d].mcpServers) // {}) | to_entries[] | "\(.key) \(.value.url // "")"' \
        "$HOME/.claude.json" 2>/dev/null | grep -m1 '/tidewave/mcp')
fi
[ -n "$ENTRY" ] || exit 0
NAME=${ENTRY%% *}
URL=${ENTRY#* }

emit() { # emit <warning for the human> <context for the session>; exit 0 never blocks.
  jq -n --arg m "$1" --arg c "$2" \
    '{systemMessage:$m,hookSpecificOutput:{hookEventName:"SessionStart",additionalContext:$c}}'
  exit 0
}

# Judge by whether the connection succeeded, not by the status code alone: a Tidewave
# registered with the sse transport can answer this POST with a non-200 while perfectly
# healthy, and the failure this hook exists to catch is a dev server that isn't there.
CODE=$(curl -s -m 2 -o /dev/null -w '%{http_code}' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  --data '{"jsonrpc":"2.0","id":1,"method":"ping"}' \
  "$URL" 2>/dev/null)
RC=$?

if [ "$RC" -ne 0 ]; then
  emit "Tidewave: nothing is listening at $URL — start this project's dev server, then reconnect $NAME in /mcp." \
    "Tidewave pre-flight: nothing is listening at $URL, so this project's dev server is not running. Every mcp__tidewave__* tool call will fail. The human has been shown a warning; in your first reply, before starting any task, ask them to start the dev server (\`mix phx.server\`, or whatever command this repo's CLAUDE.md names) and then reconnect the $NAME MCP server with /mcp. Do not route around it with \`mix run\`, \`iex\` or a second server process, and do not start the server yourself."
fi

if [ "$CODE" != "200" ]; then
  emit "Tidewave: $URL answered HTTP $CODE, not as a Tidewave endpoint — check what is on that port and the MCP transport." \
    "Tidewave pre-flight: $URL answered HTTP $CODE rather than a JSON-RPC result. Something is listening on that port, but it is not responding as a Tidewave MCP endpoint — most likely a different app on the port, or a transport mismatch (sse vs http) in the MCP server config. Expect mcp__tidewave__* calls to fail, and surface this to the human before relying on them."
fi

exit 0
