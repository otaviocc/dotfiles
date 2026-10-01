# tmux-agents

Status of coding-agent panes (◆ waiting, ● running, ○ idle), with instant jump.

State lives in pane options, set by agent hooks, so every view is a single
`tmux list-panes` call rather than a scrape of panes or processes:

| Option | Meaning |
|---|---|
| `@agent_status` | `running`, `waiting` or `idle` |
| `@agent_since` | epoch of the last status change |
| `@agent_pid` | the agent process, so a reader can prove it is still alive |
| `@agent_session` | who owns the pane, so a second agent cannot overwrite it |

`scripts/live-panes.sh` is the **one** place that turns those options into a list
of live agents; `summary.sh`, `list.sh` and `next-waiting.sh` all read it instead
of `list-panes` directly. That is deliberate — when they each filtered for
themselves, the status bar would count a dead agent the picker refused to show
and `prefix+a` could not jump to.

Two kinds of staleness it exists to stop:

- **A killed or crashed agent.** Claude Code's `SessionEnd` hook does not fire
  then, so the pane options outlive the process. `live-panes.sh` drops any pane
  whose `@agent_pid` fails `kill -0`, which is also why a pane with a status but
  no pid does not count: nothing proves the agent is there.
- **A second agent in the same pane.** A nested `claude -p` from a script or a
  git hook inherits `$TMUX_PANE`, so its hooks report over the session that owns
  the pane, and its `SessionEnd` clears the pane while the real agent is still
  working. `set-status.sh` records the owner's `session_id` and ignores reports
  from anyone else while the owner's pid is alive.

## Install
    # ~/.tmux.conf
    set -g mouse on
    set -g status-right '#{agents_summary} %H:%M'
    run-shell ~/.config/tmux/plugins/tmux-agents/agents.tmux

Claude Code needs no setup: the `claude` package ships a hooks-only plugin
(`claude/.claude/skills/tmux-agents/`) that Claude Code auto-loads from
`~/.claude/skills/`, so `settings.json` — untracked, it holds tokens — is never
touched.

Other agents: call `scripts/set-status.sh running|waiting|idle|clear` from their hooks.

## Keys (prefix)
- `a` jump to the agent waiting longest
- `A` fzf picker with live preview (needs fzf)
- click the status-bar summary to open the picker

Each row is labelled with `pane_title`, which Claude Code sets to what it is
working on, falling back to the pane's path when nothing has set it.

Options: `@agents-key-pick`, `@agents-key-next`. Requires tmux >= 3.2.
