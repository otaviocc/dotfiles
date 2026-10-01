#!/usr/bin/env bash
# Prints: <pane_id>\t<colored line>, waiting first (longest waiting first), then running, then idle.
# Which panes are listed at all is live-panes.sh's call, not this script's.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$DIR/live-panes.sh" | awk -F'\t' -v now="$(date +%s)" '
function age(s,  d) { if (s == "") return "-"; d = now - s
  if (d < 60) return d "s"; if (d < 3600) return int(d/60) "m"; return int(d/3600) "h" }
{
  if ($2 == "waiting")      { r = 0; c = "\033[33m"; i = "◆" }
  else if ($2 == "running") { r = 1; c = "\033[32m"; i = "●" }
  else                      { r = 2; c = "\033[90m"; i = "○" }
  printf "%d\t%d\t%s\t%s%s %-8s\033[0m  %-14s %5s  %s\n", r, ($3 == "" ? 0 : $3), $1, c, i, $2, $5, age($3), $4
}' | sort -t$'\t' -k1,1n -k2,2n | cut -f3-
