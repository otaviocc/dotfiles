#!/usr/bin/env bash
# Jump to the agent that has been waiting longest (excluding the current pane).
# Tab-delimited on purpose: splitting live-panes.sh's rows on whitespace would
# shift every column the moment @agent_since was empty, and silently match
# nothing while the status bar still showed a waiting agent.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cur=$(tmux display-message -p '#{pane_id}')
next=$("$DIR/live-panes.sh" |
  awk -F'\t' -v cur="$cur" '$2 == "waiting" && $1 != cur { print ($3 == "" ? 0 : $3) "\t" $1 }' |
  sort -n | head -n1 | cut -f2)
if [ -n "$next" ]; then "$DIR/jump.sh" "$next"; else tmux display-message "No agents waiting"; fi
