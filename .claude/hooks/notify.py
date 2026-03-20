#!/usr/bin/env python3
"""Claude Code desktop notification hook.

Works for both Notification and Stop hook events.
Prefers terminal-notifier for richer click actions when available and falls
back to AppleScript notifications otherwise. Notifications only fire when
Claude is not running in the active iTerm2 context. Inside tmux, that means
the active pane in the active window; background panes in the focused tab
should still notify.
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
CLICK_HANDLER = os.path.join(os.path.dirname(__file__), "notify_click.py")
TERMINAL_NOTIFIER = shutil.which("terminal-notifier")


def current_iterm_session_uuid() -> Optional[str]:
    """Return the current iTerm session UUID from the environment."""
    session_id = os.environ.get("ITERM_SESSION_ID", "")
    # ITERM_SESSION_ID format: w0t0p0:UUID
    match = re.search(r":([A-F0-9-]+)$", session_id, re.IGNORECASE) if session_id else None
    return match.group(1).upper() if match else None


def active_iterm_session_uuid() -> Optional[str]:
    """Return the focused iTerm session UUID, or a sentinel for other frontmost apps."""

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
    """Return True when this Claude process is in the focused iTerm tab."""
    our_uuid = current_iterm_session_uuid()
    active_uuid = active_iterm_session_uuid()

    if active_uuid == OTHER_FRONTMOST_APP:
        return False
    if not active_uuid or not our_uuid:
        return True  # Can't determine, assume active (don't spam)
    return active_uuid == our_uuid


def is_active_tmux_context() -> Optional[bool]:
    """Return True when this tmux pane is the currently focused pane, else False.

    Returns None when tmux state cannot be determined.
    """
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
    """Return True when Claude is already visible in the active UI context."""
    if not is_active_iterm_tab():
        return False

    tmux_active = is_active_tmux_context()
    if tmux_active is None:
        return True
    return tmux_active


def run(args: list[str]) -> subprocess.CompletedProcess:
    """Run a subprocess with captured text output."""
    return subprocess.run(args, capture_output=True, text=True)


def tmux_value(target: str, fmt: str) -> Optional[str]:
    """Return a tmux format value for the given target."""
    result = run(["tmux", "display-message", "-p", "-t", target, fmt])
    if result.returncode != 0:
        return None

    value = result.stdout.strip()
    return value if value else None


def notification_context() -> dict[str, str]:
    """Return the context needed to restore iTerm/tmux on notification click."""
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
    """Build the click handler command for terminal-notifier."""
    if not os.path.isfile(CLICK_HANDLER):
        return None

    command = [CLICK_HANDLER]
    for key in ("iterm_session", "client_tty", "session_name", "window_id", "pane_id"):
        value = context.get(key)
        if value:
            command.extend([f"--{key.replace('_', '-')}", value])

    return " ".join(shlex.quote(part) for part in command)


def native_notify(title: str, message: str, sound: str) -> None:
    """Send a native AppleScript notification."""
    script = (
        f"display notification {json.dumps(message)} "
        f"with title {json.dumps(title)} "
        f'sound name "{sound}"'
    )
    subprocess.run(["osascript", "-e", script])


def terminal_notify(title: str, message: str, sound: str, context: dict[str, str]) -> bool:
    """Send a terminal-notifier notification if available."""
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

    result = subprocess.run(args)
    return result.returncode == 0


def notify(title: str, message: str, sound: str = "Glass") -> None:
    if is_active_context():
        return

    context = notification_context()
    if terminal_notify(title, message, sound, context):
        return
    native_notify(title, message, sound)


def main() -> None:
    try:
        hook_input = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        hook_input = {}

    event = hook_input.get("hook_event_name", "")

    if event == "Notification":
        notification_type = hook_input.get("notification_type", "")
        message = hook_input.get("message", "Agent needs your attention")

        if notification_type == "permission_prompt":
            title = "Claude - Permission Needed"
        elif notification_type == "idle_prompt":
            title = "Claude - Waiting for Input"
        else:
            title = "Claude Code"

        notify(title, message, sound="Ping")

    elif event == "Stop":
        # Avoid notifying when stop is itself triggered by a stop hook
        if hook_input.get("stop_hook_active"):
            return

        last_msg = hook_input.get("last_assistant_message", "")
        if last_msg and len(last_msg) > 100:
            last_msg = last_msg[:97] + "..."

        message = last_msg if last_msg else "Agent has completed"
        notify("Claude - Done", message, sound="Ping")


if __name__ == "__main__":
    main()
