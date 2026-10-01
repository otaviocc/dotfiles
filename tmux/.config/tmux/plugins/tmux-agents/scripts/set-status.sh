#!/usr/bin/env bash
# Usage: set-status.sh running|waiting|idle|clear
# Called from agent hooks. For Claude Code that is the tmux-agents plugin in the
# claude package, which maps each event to one of these words; other agents can
# call this directly, and may pass their hook payload on stdin.
#
# The pane options are the contract live-panes.sh reads back:
#   @agent_status   running|waiting|idle
#   @agent_since    epoch of the last status change
#   @agent_pid      the agent process, so a reader can prove it is still there
#   @agent_session  who owns the pane, so a second agent cannot overwrite it
[ -n "$TMUX_PANE" ] || exit 0
s="$1"
[ -n "$s" ] || exit 0

# Who is reporting. Claude Code hands no pid to a hook, but every payload
# carries session_id, and that is the only thing that distinguishes a nested
# `claude -p` from the session that owns the pane: both resolve to the same
# agent process, because the walk below stops at the pane's own child.
session=""
[ -t 0 ] || session=$(grep -o '"session_id":"[^"]*"' | head -n1 | cut -d'"' -f4)

owner=$(tmux show-option -pqv -t "$TMUX_PANE" @agent_session)
owner_pid=$(tmux show-option -pqv -t "$TMUX_PANE" @agent_pid)
owner_live=false
[ -n "$owner_pid" ] && kill -0 "$owner_pid" 2>/dev/null && owner_live=true

if ! { $owner_live && [ -n "$session" ] && [ "$owner" = "$session" ]; }; then
  # Not already the owner, so work out which process we are. The agent is the
  # ancestor of this hook that is a direct child of the pane's shell — true of
  # any agent run in a pane, not just Claude Code. Costs a few `ps` calls, and
  # only happens once per session: every later report takes the fast path above.
  pane_pid=$(tmux display-message -p -t "$TMUX_PANE" '#{pane_pid}' 2>/dev/null) || exit 0
  pid=""
  p=$$
  while :; do
    parent=$(ps -o ppid= -p "$p" 2>/dev/null | tr -d ' ')
    [ -n "$parent" ] && [ "$parent" -gt 1 ] 2>/dev/null || break
    if [ "$parent" = "$pane_pid" ]; then pid="$p"; break; fi
    p="$parent"
  done
  me="${session:-pid:$pid}"

  # Another live agent holds this pane — a nested `claude -p`, a git hook, a
  # script. Reporting our state would overwrite the real one, and our SessionEnd
  # would clear the pane out from under an agent that is still working.
  if $owner_live && [ -n "$owner" ] && [ "$owner" != "$me" ]; then exit 0; fi

  [ -n "$pid" ] && tmux set-option -p -t "$TMUX_PANE" @agent_pid "$pid"
  tmux set-option -p -t "$TMUX_PANE" @agent_session "$me"
fi

if [ "$s" = clear ]; then
  tmux set-option -p -u -t "$TMUX_PANE" @agent_status
  tmux set-option -p -u -t "$TMUX_PANE" @agent_since
  tmux set-option -p -u -t "$TMUX_PANE" @agent_pid
  tmux set-option -p -u -t "$TMUX_PANE" @agent_session
else
  cur=$(tmux show-option -pqv -t "$TMUX_PANE" @agent_status)
  tmux set-option -p -t "$TMUX_PANE" @agent_status "$s"
  [ "$cur" = "$s" ] || tmux set-option -p -t "$TMUX_PANE" @agent_since "$(date +%s)"
fi
tmux refresh-client -S 2>/dev/null
exit 0
