#!/usr/bin/env python3
"""tmux-agents: a menu of the coding agents running in tmux, Enter jumps.

Bound to prefix+a in tmux.conf as `agents.py "#{client_name}"`. Lists every
Claude Code and OpenCode pane across all sessions with its status, project
path and session name, as a native `display-menu`:

    ◆ waiting  cc  debug-image-picker-lag  ~/Developer/tr-ios
    ● running  cc                          ~/.dotfiles
    ○ idle     oc  Fix the parser          ~/Developer/rewind

No hooks, no agent configuration. Each agent is read where it already leaves
its state:

  - Claude Code writes ~/.claude/sessions/<pid>.json for its own fleet view,
    carrying the tmux pane, `status` (busy|waiting|idle|shell), the session
    `name` and whether the user set it (`nameSource == "user"`). The file is
    undocumented and outlives a killed process, so a record only counts while
    its pid is alive *and* sits under the pane it names.
  - OpenCode records nothing that maps a process to a session or a status. It
    is found in the process tree, its status is scraped from the pane with the
    strings in OPENCODE_STATUS, and its name is the newest top-level session for
    the pane's directory in its sqlite db.

Colours are Default+ (docs/palette.md); hex stays lowercase because tmux
format-expands menu labels and `#F`, `#I`, `#W`... are legacy specifiers.

stdlib only; any failure degrades to fewer rows rather than an error.
"""

import glob
import json
import os
import sqlite3
import subprocess
import sys

STATUS = {
    # rank, glyph, colour
    "waiting": (0, "◆", "#ffe76d"),
    "running": (1, "●", "#2ea85b"),
    "idle": (2, "○", "#8e8e8e"),
}
CLAUDE_STATUS = {"busy": "running", "waiting": "waiting"}  # idle, shell -> idle

# Checked in order against the bottom of an OpenCode pane, case-insensitively.
OPENCODE_STATUS = [
    ("waiting", ("allow once", "allow always", "permission required")),
    ("running", ("esc interrupt", "esc to interrupt")),
]
OPENCODE_DB = os.path.join(
    os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share"),
    "opencode",
    "opencode.db",
)

NAME_WIDTH = 28
PATH_WIDTH = 48
HOTKEYS = "123456789abcdefghijklmnopqrstuvwxyz"


def tmux(*args):
    return subprocess.run(
        ["tmux", *args], capture_output=True, text=True
    ).stdout


def panes():
    """pane_id -> (pane_pid, pane_current_path)."""
    out = tmux("list-panes", "-a", "-F",
               "#{pane_id}\t#{pane_pid}\t#{pane_current_path}")
    result = {}
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and parts[1].isdigit():
            result[parts[0]] = (int(parts[1]), parts[2])
    return result


def processes():
    """pid -> (ppid, command basename)."""
    out = subprocess.run(["ps", "-A", "-o", "pid=,ppid=,comm="],
                         capture_output=True, text=True).stdout
    result = {}
    for line in out.splitlines():
        parts = line.split(None, 2)
        if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
            result[int(parts[0])] = (int(parts[1]), os.path.basename(parts[2]))
    return result


def lineage(pid, procs):
    """pid, then its parent, grandparent... An agent started as the pane's
    command is the pane_pid itself, so the pid has to count too."""
    seen = set()
    while pid > 1 and pid not in seen:
        yield pid
        seen.add(pid)
        if pid not in procs:
            return
        pid = procs[pid][0]


def alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        pass
    return True


def claude_agents(pane_map, procs):
    config = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    for path in glob.glob(os.path.join(config, "sessions", "*.json")):
        try:
            with open(path) as f:
                s = json.load(f)
            pid = int(s["pid"])
            pane = s["tmux"].rsplit(".", 1)[-1]
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            continue
        if s.get("kind") != "interactive" or pane not in pane_map or not alive(pid):
            continue
        # The pane id may since have been reused, or the file left behind by
        # a pid the OS has recycled: only trust it if the pid is in that pane.
        if pane_map[pane][0] not in lineage(pid, procs):
            continue
        yield {
            "tool": "cc",
            "pane": pane,
            "status": CLAUDE_STATUS.get(s.get("status"), "idle"),
            "name": (s.get("name") or "") if s.get("nameSource") == "user" else "",
            "path": s.get("cwd") or pane_map[pane][1],
            "since": s.get("statusUpdatedAt") or 0,
        }


def opencode_status(pane):
    screen = tmux("capture-pane", "-p", "-t", pane).splitlines()
    tail = "\n".join(screen[-20:]).lower()
    for status, needles in OPENCODE_STATUS:
        if any(n in tail for n in needles):
            return status
    return "idle"


def opencode_name(directory):
    try:
        db = sqlite3.connect(f"file:{OPENCODE_DB}?mode=ro", uri=True, timeout=0.2)
        try:
            row = db.execute(
                "SELECT title FROM session WHERE directory = ? AND parent_id IS NULL"
                " AND time_archived IS NULL ORDER BY time_updated DESC LIMIT 1",
                (directory,),
            ).fetchone()
        finally:
            db.close()
    except sqlite3.Error:
        return ""
    title = row[0] if row else ""
    # OpenCode's placeholder until it has summarised the first prompt.
    return "" if title.startswith("New session - ") else title


def opencode_agents(pane_map, procs):
    by_pane_pid = {pane_pid: pane for pane, (pane_pid, _) in pane_map.items()}
    for pid, (_, comm) in procs.items():
        if comm != "opencode":
            continue
        chain = list(lineage(pid, procs))
        # Skip OpenCode's own worker processes; the outermost one is the TUI.
        if any(procs.get(a, (0, ""))[1] == "opencode" for a in chain[1:]):
            continue
        pane = next((by_pane_pid[a] for a in chain if a in by_pane_pid), None)
        if pane is None:
            continue
        path = pane_map[pane][1]
        yield {
            "tool": "oc",
            "pane": pane,
            "status": opencode_status(pane),
            "name": opencode_name(path),
            "path": path,
            "since": 0,
        }


def fit(text, width, keep_end=False):
    if len(text) <= width:
        return text.ljust(width)
    return "…" + text[-(width - 1):] if keep_end else text[:width - 1] + "…"


def label(agent):
    _, glyph, colour = STATUS[agent["status"]]
    path = agent["path"]
    home = os.path.expanduser("~")
    if path == home or path.startswith(home + "/"):
        path = "~" + path[len(home):]
    # Padding is done before escaping, so a doubled `##` still renders one
    # column wide.
    name = fit(agent["name"], NAME_WIDTH).replace("#", "##")
    path = fit(path, PATH_WIDTH, keep_end=True).rstrip().replace("#", "##")
    return (f"#[fg={colour}]{glyph} {agent['status']:<7}  "
            f"#[fg=#4c4c4c]{agent['tool']}  "
            f"#[fg=#ffffff]{name}  "
            f"#[fg=#8e8e8e]{path}")


def main():
    client = sys.argv[1] if len(sys.argv) > 1 else ""
    target = ["-c", client] if client else []

    pane_map, procs = panes(), processes()
    agents = list(claude_agents(pane_map, procs))
    claimed = {a["pane"] for a in agents}
    agents += [a for a in opencode_agents(pane_map, procs) if a["pane"] not in claimed]
    if not agents:
        tmux("display-message", *target, "No agent sessions")
        return

    agents.sort(key=lambda a: (STATUS[a["status"]][0], a["since"]))
    items = []
    for key, agent in zip(HOTKEYS, agents):
        p = agent["pane"]
        items += [label(agent), key,
                  f"switch-client -t {p} ; select-window -t {p} ; select-pane -t {p}"]
    tmux("display-menu", *target, "-T", "#[align=centre] agents ",
         "-x", "C", "-y", "C", *items)


if __name__ == "__main__":
    main()
