#!/usr/bin/env bash
# Adds (idempotently) Claude Code hooks that report status to tmux.
# Usage: install-hooks.sh [--dry-run]
set -e
command -v jq >/dev/null || { echo "jq is required"; exit 1; }
S="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/set-status.sh"
S="${S/#$HOME/\$HOME}"   # keep it portable: the hook shell expands $HOME
F="$HOME/.claude/settings.json"
[ -f "$F" ] || { mkdir -p "$(dirname "$F")"; echo '{}' > "$F.new"; F="$F.new"; NEW=1; }

out=$(jq --arg s "$S" '
  def add($ev; $arg):
    .hooks[$ev] = ((.hooks[$ev] // [])
      | map(select(any(.hooks[]?; (.command // "") | contains("set-status.sh")) | not))
      + [{hooks: [{type: "command", command: ($s + " " + $arg)}]}]);
  .hooks //= {}
  | add("SessionStart"; "idle")
  | add("UserPromptSubmit"; "running")
  | add("PreToolUse"; "running")
  | add("PostToolUse"; "running")
  | add("Notification"; "notify")
  | add("Stop"; "idle")
  | add("SessionEnd"; "clear")
' "$F")

if [ "$1" = "--dry-run" ]; then echo "$out"; else
  T="$HOME/.claude/settings.json"
  [ -z "$NEW" ] && cp "$T" "$T.bak"; echo "$out" > "$T"; rm -f "$T.new"; echo "Hooks installed in $T"
fi
