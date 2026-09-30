#!/usr/bin/env bash
# tmux-agents: show coding-agent panes, their status, and jump to them.
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
S="$CURRENT_DIR/scripts"

opt() { local v; v=$(tmux show-option -gqv "$1"); echo "${v:-$2}"; }

pick_key=$(opt @agents-key-pick A)
next_key=$(opt @agents-key-next a)

tmux bind-key "$pick_key" display-popup -E -w 85% -h 75% -T ' agents ' "$S/picker.sh"
tmux bind-key "$next_key" run-shell -b "$S/next-waiting.sh"

# Clicking the status-bar summary opens the picker; anywhere else keeps the default behaviour.
tmux bind-key -n MouseDown1Status if-shell -F '#{==:#{mouse_status_range},agents}' \
  "display-popup -E -w 85% -h 75% -T ' agents ' '$S/picker.sh'" \
  'select-window -t='

# Replace #{agents_summary} in status-left/right with the live summary.
for o in status-left status-right; do
  v=$(tmux show-option -gqv "$o")
  if [[ $v == *'#{agents_summary}'* ]]; then
    tmux set-option -g "$o" "${v//'#{agents_summary}'/#($S/summary.sh)}"
  fi
done
