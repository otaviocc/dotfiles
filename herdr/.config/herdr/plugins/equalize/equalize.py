#!/usr/bin/env python3
"""equalize: make every pane in the current tab the same size.

Bound to prefix+= in config.toml. herdr has no "even layout" command and
`pane resize` cannot set a ratio, only nudge one: `--direction right
--amount 0.1` moves the divider on the pane's right edge by 0.1 of the
split's extent (ratios clamp to 0.1..0.9). So for each split this computes
the target ratio and moves its divider by the difference, from a pane whose
edge *is* that divider.

`pane layout` reports a flat list of split and pane rects, not a tree, so the
tree is rebuilt by containment: a node's children are the largest rects
strictly inside it. The target for a split is the share of its own axis the
first side should get, where a chain of same-direction splits counts its
leaves and a perpendicular subtree counts as one -- three columns end up a
third each, however they were split.

Zoomed tabs are skipped: their pane rects describe the zoom, not the tiling.

stdlib only.
"""

import json
import os
import subprocess
import sys

HERDR = os.environ.get("HERDR_BIN_PATH") or "herdr"
TOLERANCE = 0.005
PASSES = 3
AXIS = {"right": ("x", "width"), "down": ("y", "height")}
SHRINK = {"right": "left", "down": "up"}


def herdr(*args):
    out = subprocess.run([HERDR, *args], check=True, capture_output=True, text=True)
    return json.loads(out.stdout)["result"]


def contains(outer, inner):
    return (
        outer["x"] <= inner["x"]
        and outer["y"] <= inner["y"]
        and inner["x"] + inner["width"] <= outer["x"] + outer["width"]
        and inner["y"] + inner["height"] <= outer["y"] + outer["height"]
    )


def build(layout):
    """Return the root node; splits get a two-element `children` list."""
    nodes = [dict(s, kind="split") for s in layout["splits"]]
    nodes += [dict(p, kind="pane") for p in layout["panes"]]
    for node in nodes:
        inside = [n for n in nodes if n is not node and contains(node["rect"], n["rect"])]
        if node["kind"] == "split":
            top = [n for n in inside if not any(m is not n and contains(m["rect"], n["rect"]) for m in inside)]
            pos = AXIS[node["direction"]][0]
            node["children"] = sorted(top, key=lambda n: n["rect"][pos])
    roots = [n for n in nodes if not any(m is not n and contains(m["rect"], n["rect"]) for m in nodes)]
    return roots[0] if len(roots) == 1 else None


def weight(node, direction):
    if node["kind"] == "split" and node["direction"] == direction:
        return sum(weight(c, direction) for c in node["children"])
    return 1


def leaves(node):
    if node["kind"] == "pane":
        return [node]
    return [leaf for c in node["children"] for leaf in leaves(c)]


def splits(node):
    if node["kind"] == "pane":
        return []
    return [node] + [s for c in node["children"] for s in splits(c)]


def equalize_tab(pane_id):
    """Run up to PASSES rounds of nudges; return True once every split is within tolerance."""
    for _ in range(PASSES):
        layout = herdr("pane", "layout", "--pane", pane_id)["layout"]
        if layout["zoomed"] or not layout["splits"]:
            return True
        root = build(layout)
        if root is None:
            print(f"{layout['tab_id']}: could not rebuild split tree", file=sys.stderr)
            return False
        settled = True
        for split in splits(root):
            if len(split["children"]) != 2:
                print(f"{layout['tab_id']}: {split['id']} has {len(split['children'])} children", file=sys.stderr)
                return False
            first, second = split["children"]
            direction = split["direction"]
            a, b = weight(first, direction), weight(second, direction)
            delta = a / (a + b) - split["ratio"]
            if abs(delta) <= TOLERANCE:
                continue
            settled = False
            # A pane moves its own edge, so grow from the first side's far
            # pane and shrink from the second side's near one.
            pos, size = AXIS[direction]
            if delta > 0:
                edge = max(leaves(first), key=lambda p: p["rect"][pos] + p["rect"][size])
                towards = direction
            else:
                edge = min(leaves(second), key=lambda p: p["rect"][pos])
                towards = SHRINK[direction]
            herdr(
                "pane", "resize",
                "--pane", edge["pane_id"],
                "--direction", towards,
                "--amount", f"{abs(delta):.6f}",
            )
        if settled:
            return True
    return False


def main():
    pane_id = os.environ.get("HERDR_PANE_ID") or herdr("pane", "current")["pane"]["pane_id"]
    if not equalize_tab(pane_id):
        print("current tab: not fully equalized", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
