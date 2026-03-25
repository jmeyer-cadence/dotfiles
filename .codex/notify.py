#!/usr/bin/env python3
"""Codex desktop notification helper.

Handles Codex's external `notify` callback for completed turns.
Prefers terminal-notifier on macOS and falls back to AppleScript banners.
Notifications are suppressed when Codex is already visible in the active
iTerm/tmux context.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from typing import Optional


OTHER_FRONTMOST_APP = "__OTHER_FRONTMOST_APP__"
TERMINAL_NOTIFIER = shutil.which("terminal-notifier")


def current_iterm_session_uuid() -> Optional[str]:
    session_id = os.environ.get("ITERM_SESSION_ID", "")
    match = re.search(r":([A-F0-9-]+)$", session_id, re.IGNORECASE) if session_id else None
    return match.group(1).upper() if match else None


def active_iterm_session_uuid() -> Optional[str]:
    script = f"""
tell application "System Events"
    set frontApp to name of first application process whose frontmost is true
end tell
if frontApp is not "iTerm2" then
    return "{OTHER_FRONTMOST_APP}"
end if
tell application "iTerm2"
    try
        return unique ID of current session of current tab of current window
    on error
        return ""
    end try
end tell
"""
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return None

    active_uuid = result.stdout.strip()
    if active_uuid == OTHER_FRONTMOST_APP:
        return OTHER_FRONTMOST_APP
    return active_uuid.upper() if active_uuid else None


def is_active_iterm_tab() -> bool:
    our_uuid = current_iterm_session_uuid()
    active_uuid = active_iterm_session_uuid()

    if active_uuid == OTHER_FRONTMOST_APP:
        return False
    if not active_uuid or not our_uuid:
        return True
    return active_uuid == our_uuid


def is_active_tmux_context() -> Optional[bool]:
    tmux_pane = os.environ.get("TMUX_PANE")
    if not tmux_pane:
        return None

    result = subprocess.run(
        [
            "tmux",
            "display-message",
            "-p",
            "-t",
            tmux_pane,
            "#{session_attached}\t#{window_active}\t#{pane_active}",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None

    parts = result.stdout.strip().split("\t")
    if len(parts) != 3:
        return None

    session_attached, window_active, pane_active = parts
    if session_attached == "0":
        return False
    return window_active == "1" and pane_active == "1"


def is_active_context() -> bool:
    if not is_active_iterm_tab():
        return False

    tmux_active = is_active_tmux_context()
    if tmux_active is None:
        return True
    return tmux_active


def truncate(message: str, limit: int = 180) -> str:
    if len(message) <= limit:
        return message
    return message[: limit - 3] + "..."


def native_notify(title: str, message: str, sound: str) -> None:
    script = (
        f"display notification {json.dumps(message)} "
        f"with title {json.dumps(title)} "
        f'sound name "{sound}"'
    )
    subprocess.run(["osascript", "-e", script], capture_output=True, text=True)


def terminal_notify(title: str, message: str, sound: str, group: Optional[str]) -> bool:
    if not TERMINAL_NOTIFIER:
        return False

    args = [
        TERMINAL_NOTIFIER,
        "-title",
        title,
        "-message",
        message,
        "-sound",
        sound,
        "-activate",
        "com.googlecode.iterm2",
    ]
    if group:
        args.extend(["-group", group])

    subprocess.run(args, capture_output=True, text=True)
    return True


def notify(title: str, message: str, sound: str = "Ping", group: Optional[str] = None) -> None:
    if is_active_context():
        return

    message = truncate(message)
    if terminal_notify(title, message, sound, group):
        return
    native_notify(title, message, sound)


def main() -> int:
    if len(sys.argv) < 2:
        return 0

    try:
        payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        return 0

    if payload.get("type") != "agent-turn-complete":
        return 0

    last_message = (payload.get("last-assistant-message") or "").strip()
    input_messages = payload.get("input-messages") or []
    first_input = input_messages[0].strip() if input_messages else ""

    title = "Codex - Done"
    message = last_message or first_input or "Agent has completed"
    thread_id = payload.get("thread-id")
    group = f"codex-{thread_id}" if thread_id else None

    notify(title, message, group=group)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
