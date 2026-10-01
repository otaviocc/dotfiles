#!/usr/bin/env bash
# Usage: set-status.sh running|waiting|idle|clear
# Called from agent hooks. For Claude Code that is the tmux-agents plugin in the
# claude package, which maps each event to one of these words; other agents can
# call this directly.
[ -n "$TMUX_PANE" ] || exit 0
s="$1"

if [ "$s" = clear ]; then
  tmux set-option -p -u -t "$TMUX_PANE" @agent_status
  tmux set-option -p -u -t "$TMUX_PANE" @agent_since
else
  cur=$(tmux show-option -pqv -t "$TMUX_PANE" @agent_status)
  tmux set-option -p -t "$TMUX_PANE" @agent_status "$s"
  [ "$cur" = "$s" ] || tmux set-option -p -t "$TMUX_PANE" @agent_since "$(date +%s)"
fi
tmux refresh-client -S 2>/dev/null
exit 0
