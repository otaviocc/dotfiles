#!/usr/bin/env bash
# Prints: <pane_id>\t<colored line>, waiting first (longest waiting first), then running, then idle.
T=$'\t'
tmux list-panes -a -F "#{pane_id}${T}#{@agent_status}${T}#{@agent_since}${T}#{pane_current_command}${T}#{session_name}:#{window_index}.#{pane_index}${T}#{pane_current_path}" |
awk -F'\t' -v now="$(date +%s)" -v home="$HOME" '
function age(s,  d) { if (s == "") return "-"; d = now - s
  if (d < 60) return d "s"; if (d < 3600) return int(d/60) "m"; return int(d/3600) "h" }
$2 == "" { next }
$4 ~ /^-?(zsh|bash|fish|sh|dash|nu)$/ { next }   # agent exited, stale state
{
  if ($2 == "waiting")      { r = 0; c = "\033[33m"; i = "◆" }
  else if ($2 == "running") { r = 1; c = "\033[32m"; i = "●" }
  else                      { r = 2; c = "\033[90m"; i = "○" }
  p = $6; sub("^" home, "~", p)
  printf "%d\t%d\t%s\t%s%s %-8s\033[0m  %-14s %5s  %s\n", r, ($3 == "" ? 0 : $3), $1, c, i, $2, $5, age($3), p
}' | sort -t$'\t' -k1,1n -k2,2n | cut -f3-
