#!/usr/bin/env bash
# Status-bar segment, e.g. "◆2 ●1 ○3". Clickable (range "agents").
# Counts come from live-panes.sh, the same source the picker reads, so the bar
# cannot advertise an agent the picker will not show.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
out=$("$DIR/live-panes.sh" | awk -F'\t' '
  $2=="waiting"{w++} $2=="running"{r++} $2=="idle"{i++}
  END { if (w) printf "#[fg=#ffe76d]◆%d ", w
        if (r) printf "#[fg=#2ea85b]●%d ", r
        if (i) printf "#[fg=#4c4c4c]○%d ", i }')
[ -n "$out" ] && printf '#[range=user|agents]%s#[norange,default]' "$out"
