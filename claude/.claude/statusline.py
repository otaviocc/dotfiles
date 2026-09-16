#!/usr/bin/env python3
"""Claude Code statusline.

Reads the status JSON from stdin (schema documented in Claude Code's
`statusLine` help) and prints one line:

    Opus 5 · high  ·  .dotfiles master  ·  5h 47% 2h13m  ·  wk 12% 3d4h  ·  ctx 71%

Each usage percentage carries a countdown to its window reset. Claude Code
re-runs this on every message and tool call, but not on a timer, so a countdown
can read stale while the session sits idle -- `refreshInterval` would fix that,
and it lives in the untracked per-machine `settings.json`.

Segments drop out silently when their input is missing:
  - `effort` is absent on models without reasoning effort.
  - `rate_limits` is absent for API-key / Bedrock / Vertex sessions, and each
    window disappears once its `resets_at` has passed.
  - `context_window.used_percentage` is null until the first API response.

Colours are Catppuccin Mocha (docs/palette.md). Truecolor escapes only, so the
line does not depend on how the terminal maps the ANSI slots.

stdlib only; any unexpected input prints nothing and exits 0 so a bad payload
can never wedge the TUI.
"""

import json
import os
import re
import sys
import time

# Catppuccin Mocha, from docs/palette.md.
OVERLAY1 = "#7f849c"  # overlay1  -- labels, dim text
SURFACE2 = "#585b70"  # surface2  -- separators
MAUVE = "#cba6f7"  # mauve     -- accent: model, branch
LAVENDER = "#b4befe"  # lavender  -- directory (mirrors the zsh prompt)
YELLOW = "#f9e2af"  # yellow    -- warning heat
RED = "#f38ba8"  # red       -- critical heat

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
        return RED
    if pct >= 80:
        return YELLOW
    if pct >= 60:
        return MAUVE
    return OVERLAY1


def visible_len(text):
    return len(_ESCAPE_RE.sub("", text))


def seg_model(data):
    model = data.get("model") or {}
    name = model.get("display_name")
    if not name:
        return None
    out = fg(MAUVE, name, bold=True)
    level = (data.get("effort") or {}).get("level")
    if level:
        out += fg(OVERLAY1, f" · {level}")
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
    out = fg(LAVENDER, name)
    label = workspace.get("git_worktree") or _branch(current)
    if label:
        out += " " + fg(MAUVE, label)
    return out


def _limit(window):
    if not window:
        return None
    pct = window.get("used_percentage")
    if pct is None:
        return None
    return pct


def _countdown(window):
    """Compact time left until a rate-limit window resets, or None."""
    if not window:
        return None
    try:
        left = float(window.get("resets_at")) - time.time()
    except (TypeError, ValueError):
        return None
    if left <= 0:
        return None
    minutes = int(left // 60)
    if minutes < 1:
        return "<1m"
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    if days:
        return f"{days}d{hours}h" if hours else f"{days}d"
    if hours:
        return f"{hours}h{minutes}m" if minutes else f"{hours}h"
    return f"{minutes}m"


def seg_rate(data, key, label, resets=True):
    limits = data.get("rate_limits")
    if not limits:
        return None
    window = limits.get(key)
    pct = _limit(window)
    if pct is None:
        return None
    out = fg(OVERLAY1, f"{label} ") + fg(heat(pct), f"{pct:.0f}%")
    if resets:
        left = _countdown(window)
        if left:
            out += fg(OVERLAY1, f" {left}")
    return out


def seg_ctx(data):
    pct = (data.get("context_window") or {}).get("used_percentage")
    if pct is None:
        return None
    return fg(OVERLAY1, "ctx ") + fg(heat(pct), f"{pct:.0f}%")


def build(data, resets=True):
    builders = [
        seg_model,
        seg_dir,
        lambda d: seg_rate(d, "five_hour", "5h", resets),
        lambda d: seg_rate(d, "seven_day", "wk", resets),
        seg_ctx,
    ]
    return [s for s in (b(data) for b in builders) if s]


def main():
    data = json.load(sys.stdin)

    segments = build(data)
    if not segments:
        return

    sep = fg(SURFACE2, "  ·  ")

    def render(segs):
        return sep.join(segs)

    line = render(segments)

    try:
        columns = int(os.environ.get("COLUMNS", "0"))
    except ValueError:
        columns = 0
    # Shed the reset countdowns, then dir+branch, then model, when the line
    # overflows -- the usage numbers are the point.
    if columns and visible_len(line) > columns:
        segments = build(data, resets=False)
        line = render(segments)
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
