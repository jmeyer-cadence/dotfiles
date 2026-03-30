#!/usr/bin/env python3
"""Refresh Codex tmux pane-to-thread mappings from live Codex processes."""

import glob
import json
import os
import sqlite3
import subprocess
import tempfile
from typing import Optional


RESURRECT_MAP_PATH = os.path.expanduser("~/.codex/resurrect_sessions.json")
LOG_DB_GLOB = os.path.expanduser("~/.codex/logs_*.sqlite")
PANE_FORMAT = "#{session_name}:#{window_index}:#{pane_index}\t#{pane_tty}\t#{pane_current_command}"


def tmux_panes() -> list[tuple[str, str, str]]:
    try:
        result = subprocess.run(
            ["tmux", "list-panes", "-a", "-F", PANE_FORMAT],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return []

    if result.returncode != 0:
        return []

    panes: list[tuple[str, str, str]] = []
    for line in result.stdout.splitlines():
        stable_id, pane_tty, pane_command = (line.split("\t", 2) + ["", ""])[:3]
        if stable_id and pane_tty:
            panes.append((stable_id, pane_tty, pane_command))
    return panes


def load_resurrect_map() -> dict[str, str]:
    try:
        with open(RESURRECT_MAP_PATH) as handle:
            data = json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}

    if not isinstance(data, dict):
        return {}

    return {key: value for key, value in data.items() if isinstance(key, str) and isinstance(value, str)}


def log_db_paths() -> list[str]:
    return sorted(glob.glob(LOG_DB_GLOB), key=os.path.getmtime, reverse=True)


def codex_pid_for_tty(pane_tty: str) -> Optional[str]:
    tty_name = os.path.basename(pane_tty)
    if not tty_name:
        return None

    try:
        result = subprocess.run(
            ["ps", "-t", tty_name, "-o", "pid=,command="],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None

    if result.returncode != 0:
        return None

    pid = None
    for line in result.stdout.splitlines():
        columns = line.strip().split(None, 1)
        if len(columns) != 2:
            continue
        candidate_pid, command = columns
        if "codex" in command:
            pid = candidate_pid

    return pid


def thread_id_for_pid(codex_pid: str, db_paths: list[str]) -> Optional[str]:
    process_uuid = f"pid:{codex_pid}:%"
    query = """
        SELECT thread_id
        FROM logs
        WHERE process_uuid LIKE ?
          AND thread_id IS NOT NULL
          AND thread_id != ''
        ORDER BY ts DESC, ts_nanos DESC, id DESC
        LIMIT 1
    """

    for db_path in db_paths:
        try:
            with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as connection:
                row = connection.execute(query, (process_uuid,)).fetchone()
        except sqlite3.Error:
            continue

        if row and row[0]:
            return str(row[0])

    return None


def write_resurrect_map(resurrect_map: dict[str, str]) -> None:
    directory = os.path.dirname(RESURRECT_MAP_PATH) or "."
    os.makedirs(directory, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        dir=directory,
        prefix=".resurrect_sessions.",
        suffix=".json",
        delete=False,
    ) as handle:
        json.dump(resurrect_map, handle, indent=2, sort_keys=True)
        handle.write("\n")
        temp_path = handle.name

    os.replace(temp_path, RESURRECT_MAP_PATH)


def main() -> int:
    panes = tmux_panes()
    if not panes:
        return 0

    db_paths = log_db_paths()
    if not db_paths:
        return 0

    resurrect_map = load_resurrect_map()
    changed = False

    current_stable_ids = {stable_id for stable_id, _pane_tty, _pane_command in panes}
    codex_stable_ids = {
        stable_id for stable_id, _pane_tty, pane_command in panes if "codex" in pane_command
    }
    for stable_id in list(resurrect_map):
        if stable_id in current_stable_ids and stable_id not in codex_stable_ids:
            resurrect_map.pop(stable_id)
            changed = True

    for stable_id, pane_tty, pane_command in panes:
        if "codex" not in pane_command:
            continue

        codex_pid = codex_pid_for_tty(pane_tty)
        if not codex_pid:
            continue

        thread_id = thread_id_for_pid(codex_pid, db_paths)
        if thread_id and resurrect_map.get(stable_id) != thread_id:
            resurrect_map[stable_id] = thread_id
            changed = True

    if changed:
        write_resurrect_map(resurrect_map)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
