#!/usr/bin/env bash
# Usage: jump.sh <pane_id>
p="$1"; [ -n "$p" ] || exit 1
sess=$(tmux display-message -p -t "$p" '#{session_name}') || exit 1
win=$(tmux display-message -p -t "$p" '#{window_id}')
tmux switch-client -t "$sess" \; select-window -t "$win" \; select-pane -t "$p"
