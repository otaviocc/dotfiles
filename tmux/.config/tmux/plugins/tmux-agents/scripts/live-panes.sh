#!/usr/bin/env bash
# The one place that decides which panes hold a live agent, so the status bar,
# the picker and the jump key can never disagree about it.
#
# Prints one tab-separated row per live agent pane:
#   <pane_id>  <status>  <since epoch>  <label>  <session:window.pane>
#
# A pane counts only when @agent_status is set *and* the @agent_pid recorded
# beside it is still alive. Claude Code's SessionEnd hook does not fire when it
# is killed or crashes, so the pane options outlive the process; checking the pid
# is what keeps a dead agent out of the status bar. A pane carrying a status but
# no pid is dropped for the same reason — there is nothing there to prove the
# agent is still running.
T=$'\t'
tmux list-panes -a -F "#{pane_id}${T}#{@agent_status}${T}#{@agent_since}${T}#{@agent_pid}${T}#{pane_title}${T}#{session_name}:#{window_index}.#{pane_index}${T}#{pane_current_path}${T}#{host}${T}#{host_short}" |
while IFS=$'\t' read -r id status since pid title target path host host_short; do
  [ -n "$status" ] || continue
  [ -n "$pid" ] || continue
  kill -0 "$pid" 2>/dev/null || continue

  # Claude Code overwrites pane_title with what it is working on, which is worth
  # more in the picker than the cwd. tmux seeds the title with the hostname, so
  # fall back to the path when nothing has set it — the same test tmux.conf's
  # pane-border-format uses.
  label="$title"
  case "$label" in
    "" | "$host" | "$host_short") label="${path/#$HOME/~}" ;;
  esac

  printf '%s\t%s\t%s\t%s\t%s\n' "$id" "$status" "$since" "$label" "$target"
done
