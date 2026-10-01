# AGENTS.md

Personal agent skills, shared between Claude Code and opencode. Each skill is a
folder here bundling a `SKILL.md` (instructions) with whatever it shells out to.
None of the three remaining skills ships a script: they call `curl`, the `hunk`
binary and `gh` respectively, so there is nothing here to install.

Everything here is a skill. That is worth stating because it was not always
true: `tmux-agents/` was a hooks-only Claude Code *plugin* parked in this
directory, since `~/.claude/skills/` is where Claude Code auto-loads plugins
from. It is gone, but the reason it lived here still applies to any future
plugin — see the `claude` entry in the repo-root `AGENTS.md`.

## Skills in this repo

| Skill | Implementation | Purpose |
|-------|-----------------|---------|
| `brrr` | none (curl only) | Send a push notification to the user's devices via the Brrr API |
| `hunk` | none (shells out to the `hunk` binary) | Load Hunk's own review skill (`hunk skill path`) and use it for a code review |
| `pull-request` | none (shells out to `gh`) | Draft a concise PR description and open it as a draft PR after confirmation |

This directory used to also hold a set of media-library skills —
`organize-movies`, `organize-tv`, `organize-kids-shows`, `add-episode-titles`
and `flac-to-alac`. They are gone; git history before this commit has them, and
the first four were already thin wrappers over
[otaviocc/acervo](https://github.com/otaviocc/acervo), which still has the
filesystem and naming logic in its own repo. Nothing here depends on `acervo`
any more.

## Where these are stowed

These live in the `claude` package at `claude/.claude/skills/`, stowed to
`~/.claude/skills/`. Claude Code reads that directory natively. opencode does
**not**, despite its own bundled docs listing `~/.claude/skills` under "External
skills (auto-loaded)" — as of 1.18.29 nothing there is picked up, symlinked or
not. The `opencode` package registers the directory explicitly instead:

```jsonc
"skills": { "paths": ["~/.claude/skills"] }
```

A leading `~` is expanded; `$HOME` is not. Verify with `opencode debug skill`,
which prints every skill it can see and where each was loaded from.

On the Fedora box stow has folded **the whole `claude` package**, one level
higher than you might expect: `~/.claude` itself is a single symlink to
`.dotfiles/claude/.claude`, so adding or deleting a skill here takes effect with
no re-stow. The flip side is that everything Claude Code writes under
`~/.claude` — `settings.json`, `skills/synced/`, session state — lands *inside
this repo*, which is why `.gitignore` blanket-ignores `/claude/.claude/*` and
negates only the three tracked paths. Those writes do not break the fold, since
they just land in the already-linked directory; stowing onto a machine that
already has a real `~/.claude` unfolds into per-entry symlinks instead, and
there a new skill does need `./install.sh claude`.

## Skills NOT in this repo

Two sets of skills show up in Claude Code next to this package's and are **not**
tracked here, so they will not survive a bootstrap onto a new machine:

**Account-synced skills** land in `skills/synced/<bucket>/`, which `.gitignore`
excludes because Claude Code writes it. These are not files to delete — the
directory is a cache of what the Claude account holds, and a deleted folder is
restored on the next sync. `manifest.json` there records each one's `source` and
`creatorType`; the ones with `creatorType: "user"` are the user's own uploads
(`bear-cli`, `code-snippet-image` and `jellyfin-library-cards` at the time of
writing) and have to be removed from the account's skill settings, not from disk.

**Tool-installed skills**, on the macOS machine only:

| Skill | Where it actually lives |
|-------|-------------------------|
| `stash-cli` | the Stash project itself (`CLI`'s own skill); deliberately untracked here so the docs never drift from the binary |
| `supacode-cli`, `supacode-deeplinks` | real directories, installed by Supacode itself |
| `swift-concurrency`, `swift-testing-expert`, `swiftui-expert-skill`, `xcode-disk-cleanup` | symlinks into `~/.agents/skills/`, installed as Claude Code plugins |

Anything tool-installed lands in `~/.claude/skills/` as a real directory, which
is what forces stow to unfold the directory on that machine.

## Commit messages

Follow the seven rules (cbea.ms/git-commit); nothing enforces this, it's discipline:

- Subject: imperative mood ("Add", "Fix", not "Added"/"Adds"), capitalized, ≤50 chars, no trailing period. Verified by `git log`.
- Blank line between subject and body; wrap the body at 72 chars.
- Body explains what and why, not how. A single cohesive change gets prose; a commit grouping several distinct changes gets - bullets.
