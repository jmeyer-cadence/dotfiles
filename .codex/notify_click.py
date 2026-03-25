#!/usr/bin/env python3
"""Restore the relevant iTerm/tmux context when a Codex notification is clicked."""

import argparse
import os
import shutil
import subprocess
from typing import Optional


def resolve_command(command: str, fallbacks: list[str]) -> str:
    resolved = shutil.which(command)
    if resolved:
        return resolved

    for candidate in fallbacks:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    return command


OSASCRIPT = resolve_command("osascript", ["/usr/bin/osascript"])
TMUX = resolve_command("tmux", ["/opt/homebrew/bin/tmux", "/usr/local/bin/tmux"])


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True)


def focus_iterm_session(session_uuid: Optional[str]) -> None:
    if session_uuid:
        script = f"""
tell application "iTerm2"
    repeat with w in windows
        repeat with t in tabs of w
            repeat with s in sessions of t
                if unique ID of s is "{session_uuid}" then
                    tell w to select
                    tell t to select
                    tell s to select
                    return "focused"
                end if
            end repeat
        end repeat
    end repeat
end tell
"""
        result = run([OSASCRIPT, "-e", script])
        if result.returncode == 0 and result.stdout.strip() == "focused":
            return

    run([OSASCRIPT, "-e", 'tell application "iTerm2" to activate'])


def tmux_value(target: str, fmt: str) -> Optional[str]:
    result = run([TMUX, "display-message", "-p", "-t", target, fmt])
    if result.returncode != 0:
        return None

    value = result.stdout.strip()
    return value if value else None


def first_client_for_session(session_name: Optional[str]) -> Optional[str]:
    if not session_name:
        return None

    result = run([TMUX, "list-clients", "-F", "#{client_tty}\t#{session_name}"])
    if result.returncode != 0:
        return None

    for line in result.stdout.splitlines():
        if not line:
            continue
        client_tty, _, attached_session = line.partition("\t")
        if attached_session == session_name and client_tty:
            return client_tty
    return None


def client_exists(client_tty: Optional[str]) -> bool:
    if not client_tty:
        return False

    result = run([TMUX, "list-clients", "-F", "#{client_tty}"])
    if result.returncode != 0:
        return False

    return client_tty in result.stdout.splitlines()


def session_name_for_target(target: Optional[str]) -> Optional[str]:
    if not target:
        return None
    return tmux_value(target, "#{session_name}")


def window_id_for_target(target: Optional[str]) -> Optional[str]:
    if not target:
        return None
    return tmux_value(target, "#{window_id}")


def target_exists(target: Optional[str]) -> bool:
    if not target:
        return False
    return run([TMUX, "display-message", "-p", "-t", target, "#{session_name}"]).returncode == 0


def switch_tmux_client(client_tty: str, target: str) -> bool:
    return run([TMUX, "switch-client", "-c", client_tty, "-t", target]).returncode == 0


def select_tmux_window(target: str) -> bool:
    return run([TMUX, "select-window", "-t", target]).returncode == 0


def focus_tmux_target(
    pane_id: Optional[str],
    window_id: Optional[str],
    session_name: Optional[str],
    client_tty: Optional[str],
) -> None:
    target = None
    if target_exists(pane_id):
        target = pane_id
    elif target_exists(window_id):
        target = window_id
    elif target_exists(session_name):
        target = session_name

    if not target:
        return

    target_session = session_name or session_name_for_target(target)
    target_window = window_id or window_id_for_target(target)
    target_client = client_tty if client_exists(client_tty) else first_client_for_session(target_session)
    if not target_client or not target_session:
        return

    if pane_id and target_exists(pane_id):
        if switch_tmux_client(target_client, pane_id):
            return

    if not switch_tmux_client(target_client, target_session):
        return

    if target_window and target_exists(target_window):
        select_tmux_window(target_window)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterm-session")
    parser.add_argument("--client-tty")
    parser.add_argument("--session-name")
    parser.add_argument("--window-id")
    parser.add_argument("--pane-id")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    focus_iterm_session(args.iterm_session)
    focus_tmux_target(args.pane_id, args.window_id, args.session_name, args.client_tty)


if __name__ == "__main__":
    main()
