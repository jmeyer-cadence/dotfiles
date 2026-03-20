#!/usr/bin/env python3
"""Restore the relevant iTerm/tmux context when a notification is clicked."""

import argparse
import subprocess
from typing import Optional


def run(args: list[str]) -> subprocess.CompletedProcess:
    """Run a subprocess with captured text output."""
    return subprocess.run(args, capture_output=True, text=True)


def focus_iterm_session(session_uuid: Optional[str]) -> None:
    """Activate iTerm and focus the window/tab containing the target session."""
    if session_uuid:
        script = f"""
tell application "iTerm2"
    activate
    repeat with w in windows
        repeat with t in tabs of w
            repeat with s in sessions of t
                if unique ID of s is "{session_uuid}" then
                    set current window to w
                    set current tab of w to t
                    return "focused"
                end if
            end repeat
        end repeat
    end repeat
end tell
"""
        result = run(["osascript", "-e", script])
        if result.returncode == 0 and result.stdout.strip() == "focused":
            return

    run(["osascript", "-e", 'tell application "iTerm2" to activate'])


def tmux_value(target: str, fmt: str) -> Optional[str]:
    """Return a tmux format value for the given target."""
    result = run(["tmux", "display-message", "-p", "-t", target, fmt])
    if result.returncode != 0:
        return None

    value = result.stdout.strip()
    return value if value else None


def first_client_for_session(session_name: Optional[str]) -> Optional[str]:
    """Return the first attached tmux client tty for a session."""
    if not session_name:
        return None

    result = run(["tmux", "list-clients", "-F", "#{client_tty}\t#{session_name}"])
    if result.returncode != 0:
        return None

    for line in result.stdout.splitlines():
        if not line:
            continue
        client_tty, _, attached_session = line.partition("\t")
        if attached_session == session_name and client_tty:
            return client_tty
    return None


def target_exists(target: Optional[str]) -> bool:
    """Return True when tmux recognizes the given target."""
    if not target:
        return False
    return run(["tmux", "display-message", "-p", "-t", target, "#{session_name}"]).returncode == 0


def switch_tmux_client(client_tty: str, target: str) -> bool:
    """Switch a tmux client to the target pane/window/session."""
    return run(["tmux", "switch-client", "-c", client_tty, "-t", target]).returncode == 0


def focus_tmux_target(
    pane_id: Optional[str],
    window_id: Optional[str],
    session_name: Optional[str],
    client_tty: Optional[str],
) -> None:
    """Restore the tmux client to the most specific available target."""
    target = None
    if target_exists(pane_id):
        target = pane_id
    elif target_exists(window_id):
        target = window_id
    elif target_exists(session_name):
        target = session_name

    if not target:
        return

    target_client = client_tty or first_client_for_session(session_name)
    if not target_client:
        return

    switch_tmux_client(target_client, target)


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
