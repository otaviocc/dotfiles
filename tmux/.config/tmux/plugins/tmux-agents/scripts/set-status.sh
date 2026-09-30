#!/usr/bin/env bash
# Usage: set-status.sh running|waiting|idle|clear|notify
# Called from agent hooks. `notify` reads the Claude Code Notification JSON on stdin.
[ -n "$TMUX_PANE" ] || exit 0
s="$1"

if [ "$s" = notify ]; then
  payload=$(cat)
  case "$payload" in
    *idle_prompt*) s=idle ;;
    *) s=waiting ;;
  esac
fi

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
