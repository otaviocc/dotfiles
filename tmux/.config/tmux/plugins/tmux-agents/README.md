# tmux-agents

Status of coding-agent panes (◆ waiting, ● running, ○ idle), with instant jump.

State lives in the pane option `@agent_status` (+ `@agent_since`), set by agent hooks, so every
view is a single `tmux list-panes` call.

## Install
    # ~/.tmux.conf
    set -g mouse on
    set -g status-right '#{agents_summary} %H:%M'
    run-shell ~/.config/tmux/plugins/tmux-agents/agents.tmux

    scripts/install-hooks.sh --dry-run   # inspect, then run without the flag (Claude Code)
    # settings.json is untracked (holds tokens), so run this once per machine

Other agents: call `scripts/set-status.sh running|waiting|idle|clear` from their hooks.

## Keys (prefix)
- `a` jump to the agent waiting longest
- `A` fzf picker with live preview (needs fzf)
- click the status-bar summary to open the picker

Options: `@agents-key-pick`, `@agents-key-next`. Requires tmux >= 3.2.
