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
import shlex
import shutil
import subprocess
import sys
from typing import Optional


OTHER_FRONTMOST_APP = "__OTHER_FRONTMOST_APP__"
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
CLICK_HANDLER = os.path.join(SCRIPT_DIR, "notify_click.py")
TERMINAL_NOTIFIER = shutil.which("terminal-notifier")
ITERM_BUNDLE_ID = "com.googlecode.iterm2"
NOTIFICATION_TIMEOUT_SECONDS = 5


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
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=NOTIFICATION_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
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
        return False
    return active_uuid == our_uuid


def is_active_tmux_context() -> bool:
    tmux_pane = os.environ.get("TMUX_PANE")
    if not tmux_pane:
        return True

    try:
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
            timeout=NOTIFICATION_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if result.returncode != 0:
        return False

    parts = result.stdout.strip().split("\t")
    if len(parts) != 3:
        return False

    session_attached, window_active, pane_active = parts
    if session_attached == "0":
        return False
    return window_active == "1" and pane_active == "1"


def is_active_context() -> bool:
    # Only suppress when we can positively confirm Codex is visible already.
    return is_active_iterm_tab() and is_active_tmux_context()


def truncate(message: str, limit: int = 180) -> str:
    if len(message) <= limit:
        return message
    return message[: limit - 3] + "..."


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=NOTIFICATION_TIMEOUT_SECONDS,
    )


def run_command(args: list[str]) -> bool:
    try:
        result = run(args)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def tmux_value(target: str, fmt: str) -> Optional[str]:
    try:
        result = run(["tmux", "display-message", "-p", "-t", target, fmt])
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None

    value = result.stdout.strip()
    return value if value else None


def notification_context() -> dict[str, str]:
    context: dict[str, str] = {}

    iterm_session = current_iterm_session_uuid()
    if iterm_session:
        context["iterm_session"] = iterm_session

    tmux_pane = os.environ.get("TMUX_PANE")
    if not tmux_pane:
        return context

    context["pane_id"] = tmux_pane

    client_tty = tmux_value(tmux_pane, "#{client_tty}")
    if client_tty:
        context["client_tty"] = client_tty

    window_id = tmux_value(tmux_pane, "#{window_id}")
    if window_id:
        context["window_id"] = window_id

    session_name = tmux_value(tmux_pane, "#{session_name}")
    if session_name:
        context["session_name"] = session_name

    return context


def click_command(context: dict[str, str]) -> Optional[str]:
    if not os.path.isfile(CLICK_HANDLER):
        return None

    command = [sys.executable or "python3", CLICK_HANDLER]
    for key in ("iterm_session", "client_tty", "session_name", "window_id", "pane_id"):
        value = context.get(key)
        if value:
            command.extend([f"--{key.replace('_', '-')}", value])

    return " ".join(shlex.quote(part) for part in command)


def native_notify(title: str, message: str, sound: str) -> bool:
    script = (
        f"display notification {json.dumps(message)} "
        f"with title {json.dumps(title)} "
        f'sound name "{sound}"'
    )
    return run_command(["osascript", "-e", script])


def terminal_notify(
    title: str,
    message: str,
    sound: str,
    context: dict[str, str],
    group: Optional[str],
) -> bool:
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
    ]
    command = click_command(context)
    if command:
        args.extend(["-execute", command])
    else:
        args.extend(["-activate", ITERM_BUNDLE_ID])
    if group:
        args.extend(["-group", group])

    return run_command(args)


def notify(title: str, message: str, sound: str = "Ping", group: Optional[str] = None) -> None:
    if is_active_context():
        return

    message = truncate(message)
    context = notification_context()
    if terminal_notify(title, message, sound, context, group):
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
