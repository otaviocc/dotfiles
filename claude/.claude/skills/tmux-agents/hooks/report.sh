#!/usr/bin/env bash
# Bridge from Claude Code hooks to the tmux-agents tmux plugin, which owns the
# writer and the pane-option contract. Exits quietly when the tmux package is
# not stowed on this machine, so a hook never fails on a claude-only box.
#
# exec keeps stdin attached: set-status.sh reads session_id off the hook payload
# to decide who owns the pane.
S="$HOME/.config/tmux/plugins/tmux-agents/scripts/set-status.sh"
[ -x "$S" ] || exit 0
exec "$S" "$@"
