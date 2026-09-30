#!/usr/bin/env bash
# Jump to the agent that has been waiting longest (excluding the current pane).
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cur=$(tmux display-message -p '#{pane_id}')
next=$(tmux list-panes -a -F '#{@agent_since} #{pane_id} #{@agent_status}' |
  awk -v cur="$cur" '$3=="waiting" && $2!=cur {print $1, $2}' | sort -n | head -n1 | cut -d' ' -f2)
if [ -n "$next" ]; then "$DIR/jump.sh" "$next"; else tmux display-message "No agents waiting"; fi
