#!/usr/bin/env bash
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v fzf >/dev/null; then echo "tmux-agents: fzf is required"; read -rn1; exit 1; fi
list=$("$DIR/list.sh")
[ -n "$list" ] || { echo "No agent sessions."; sleep 0.7; exit 0; }
sel=$(fzf --ansi --delimiter=$'\t' --with-nth=2.. --no-sort --reverse --no-info \
  --preview 'tmux capture-pane -ep -t {1} | tail -n 40' --preview-window=right:55% <<<"$list") || exit 0
"$DIR/jump.sh" "$(cut -f1 <<<"$sel")"
