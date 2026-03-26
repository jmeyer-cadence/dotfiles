#!/usr/bin/env python3
"""Save the Claude session ID for the current tmux pane on stop.

Enables tmux-resurrect to resume the correct Claude session per pane.
Keyed by session_name:window_index:pane_index, which is stable across restores.
"""

import json
import os
import subprocess
import sys
from typing import Optional


def tmux_stable_pane_id(pane: str) -> Optional[str]:
    result = subprocess.run(
        ["tmux", "display-message", "-p", "-t", pane, "#{session_name}:#{window_index}:#{pane_index}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value if value else None


def main() -> None:
    try:
        hook_input = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        hook_input = {}

    session_id = hook_input.get("session_id")
    tmux_pane = os.environ.get("TMUX_PANE")
    if not session_id or not tmux_pane:
        return

    stable_id = tmux_stable_pane_id(tmux_pane)
    if not stable_id:
        return

    resurrect_map_path = os.path.expanduser("~/.claude/resurrect_sessions.json")
    try:
        with open(resurrect_map_path) as f:
            rmap = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        rmap = {}

    rmap[stable_id] = session_id

    with open(resurrect_map_path, "w") as f:
        json.dump(rmap, f, indent=2)


if __name__ == "__main__":
    main()
