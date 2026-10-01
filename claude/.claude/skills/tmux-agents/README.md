# tmux-agents (Claude Code plugin)

Reports this session's state into the tmux pane options that the **tmux-agents
tmux plugin** reads (`tmux/.config/tmux/plugins/tmux-agents/`). That plugin owns
the writer, the pane-option contract and the UI; this half is only the hook
wiring.

Hooks-only: no skill, no agent, no MCP server, so it costs nothing in context
(`claude plugin details tmux-agents` reports `~0 tok`).

## Install

Nothing to do. `~/.claude/skills/` is stowed from the `claude` package, and
Claude Code auto-loads any plugin it finds there as `<name>@skills-dir` —
`settings.json` is never touched, which is the point: it holds API tokens and is
deliberately untracked.

Verify with `claude plugin list` (look for `tmux-agents@skills-dir`) or
`claude plugin validate claude/.claude/skills/tmux-agents`.

Disable with `claude plugin disable tmux-agents@skills-dir`.

## Event → state

| Event | State |
|---|---|
| `SessionStart` (`startup`/`resume`/`clear`/`fork`) | `idle` |
| `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PostToolUseFailure` | `running` |
| `PermissionRequest`, `Notification` (`permission_prompt`) | `waiting` |
| `Notification` (`idle_prompt`), `Stop`, `StopFailure` | `idle` |
| `SessionEnd` | `clear` |

Three of those are there to stop the pane getting stuck:

- **`SessionStart` is matched**, deliberately excluding `compact`. That source
  fires mid-turn on auto-compaction, and an unmatched hook would report `idle`
  while the agent is still working.
- **`StopFailure`** is what ends the turn on an API error (`rate_limit`,
  `overloaded`, …). Without it a rate-limited session stays `running` forever.
- **`Notification` is split by matcher** on `notification_type` rather than
  parsed from the payload, so a notification whose *body* happens to contain
  `idle_prompt` can't be misread as one.

`SessionEnd` does **not** fire when Claude Code is killed or crashes — that hole
is closed on the reader side, by the liveness check in `live-panes.sh`. See the
tmux plugin's README.
