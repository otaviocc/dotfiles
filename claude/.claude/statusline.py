#!/usr/bin/env python3
"""Claude Code statusline.

Reads the status JSON from stdin (schema documented in Claude Code's
`statusLine` help) and prints one line:

    Opus 5 · high  ·  .dotfiles master  ·  5h 47%  ·  wk 12%  ·  ctx 71%

Segments drop out silently when their input is missing:
  - `effort` is absent on models without reasoning effort.
  - `rate_limits` is absent for API-key / Bedrock / Vertex sessions, and each
    window disappears once its `resets_at` has passed.
  - `context_window.used_percentage` is null until the first API response.

Colours are Kanagawa Dragon (docs/palette.md). Truecolor escapes only -- never
ANSI bright-black, which Dragon maps to a *light* grey (see AGENTS.md).

stdlib only; any unexpected input prints nothing and exits 0 so a bad payload
can never wedge the TUI.
"""

import json
import os
import re
import sys

# Kanagawa Dragon, from docs/palette.md.
COMMENT = "#737c73"  # comment      -- labels, dim text
WHITESPACE = "#625e5a"  # whitespace   -- separators
YELLOW = "#c4b28a"  # yellow       -- accent: model, branch
VIOLET = "#8992a7"  # violet       -- directory (mirrors the zsh prompt)
VCS_CHANGED = "#dca561"  # vcs_changed  -- warning heat
VCS_REMOVED = "#c34043"  # vcs_removed  -- critical heat

RESET = "\x1b[0m"
_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")


def fg(hexcolor, text, bold=False):
    r = int(hexcolor[1:3], 16)
    g = int(hexcolor[3:5], 16)
    b = int(hexcolor[5:7], 16)
    prefix = "\x1b[1;" if bold else "\x1b["
    return f"{prefix}38;2;{r};{g};{b}m{text}{RESET}"


def heat(pct):
    """Colour for a usage percentage -- the 'Mixed heat' ramp in palette.md."""
    if pct >= 95:
        return VCS_REMOVED
    if pct >= 80:
        return VCS_CHANGED
    if pct >= 60:
        return YELLOW
    return COMMENT


def visible_len(text):
    return len(_ESCAPE_RE.sub("", text))


def seg_model(data):
    model = data.get("model") or {}
    name = model.get("display_name")
    if not name:
        return None
    out = fg(YELLOW, name, bold=True)
    level = (data.get("effort") or {}).get("level")
    if level:
        out += fg(COMMENT, f" · {level}")
    return out


def _branch(start):
    """Resolve the current branch without shelling out to git."""
    path = start
    while True:
        gitdir = os.path.join(path, ".git")
        if os.path.isdir(gitdir):
            break
        if os.path.isfile(gitdir):
            with open(gitdir, encoding="utf-8") as fh:
                line = fh.read().strip()
            if line.startswith("gitdir:"):
                target = line[len("gitdir:"):].strip()
                gitdir = target if os.path.isabs(target) else os.path.join(path, target)
                break
            return None
        parent = os.path.dirname(path)
        if parent == path:
            return None
        path = parent

    try:
        with open(os.path.join(gitdir, "HEAD"), encoding="utf-8") as fh:
            head = fh.read().strip()
    except OSError:
        return None
    if head.startswith("ref: refs/heads/"):
        return head[len("ref: refs/heads/"):]
    if head:
        return head[:7]
    return None


def seg_dir(data):
    workspace = data.get("workspace") or {}
    current = workspace.get("current_dir") or data.get("cwd")
    if not current:
        return None
    name = os.path.basename(current.rstrip("/")) or current
    out = fg(VIOLET, name)
    label = workspace.get("git_worktree") or _branch(current)
    if label:
        out += " " + fg(YELLOW, label)
    return out


def _limit(window):
    if not window:
        return None
    pct = window.get("used_percentage")
    if pct is None:
        return None
    return pct


def seg_rate(data, key, label):
    limits = data.get("rate_limits")
    if not limits:
        return None
    pct = _limit(limits.get(key))
    if pct is None:
        return None
    return fg(COMMENT, f"{label} ") + fg(heat(pct), f"{pct:.0f}%")


def seg_ctx(data):
    pct = (data.get("context_window") or {}).get("used_percentage")
    if pct is None:
        return None
    return fg(COMMENT, "ctx ") + fg(heat(pct), f"{pct:.0f}%")


def main():
    data = json.load(sys.stdin)

    builders = [
        seg_model,
        seg_dir,
        lambda d: seg_rate(d, "five_hour", "5h"),
        lambda d: seg_rate(d, "seven_day", "wk"),
        seg_ctx,
    ]
    segments = [s for s in (b(data) for b in builders) if s]
    if not segments:
        return

    sep = fg(WHITESPACE, "  ·  ")

    def render(segs):
        return sep.join(segs)

    line = render(segments)

    try:
        columns = int(os.environ.get("COLUMNS", "0"))
    except ValueError:
        columns = 0
    # Drop dir+branch, then model, when the line overflows -- the usage
    # numbers are the point.
    for drop in (seg_dir, seg_model):
        if columns and visible_len(line) > columns and len(segments) > 1:
            dropped = drop(data)
            if dropped in segments:
                segments.remove(dropped)
                line = render(segments)

    sys.stdout.write(line)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
