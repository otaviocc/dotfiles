#!/usr/bin/env bash
# Status-bar segment, e.g. "◆2 ●1 ○3". Clickable (range "agents").
out=$(tmux list-panes -a -F '#{@agent_status}' | awk '
  $1=="waiting"{w++} $1=="running"{r++} $1=="idle"{i++}
  END { if (w) printf "#[fg=#ffe76d]◆%d ", w
        if (r) printf "#[fg=#2ea85b]●%d ", r
        if (i) printf "#[fg=#4c4c4c]○%d ", i }')
[ -n "$out" ] && printf '#[range=user|agents]%s#[norange,default]' "$out"
