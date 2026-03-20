#!/usr/bin/env python3
"""Claude Code desktop notification hook.

Works for both Notification and Stop hook events.
Uses osascript to fire macOS notifications when Claude is not running in the
active iTerm2 context. Inside tmux, that means the active pane in the active
window; background panes in the focused tab should still notify.
"""

import json
import os
import re
import subprocess
import sys
from typing import Optional


OTHER_FRONTMOST_APP = "__OTHER_FRONTMOST_APP__"


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


def notify(title: str, message: str, sound: str = "Glass") -> None:
    if is_active_context():
        return

    script = (
        f"display notification {json.dumps(message)} "
        f"with title {json.dumps(title)} "
        f'sound name "{sound}"'
    )
    subprocess.run(["osascript", "-e", script])


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
