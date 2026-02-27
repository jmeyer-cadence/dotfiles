#!/usr/bin/env python3
"""Claude Code desktop notification hook.

Works for both Notification and Stop hook events.
Uses osascript to fire macOS notifications, but only when the
current iTerm2 tab is not the active/focused tab.
"""

import json
import os
import re
import subprocess
import sys


def is_active_tab() -> bool:
    """Return True if our iTerm2 tab is currently focused."""
    session_id = os.environ.get("ITERM_SESSION_ID", "")
    # ITERM_SESSION_ID format: w0t0p0:UUID
    match = re.search(r":([A-F0-9-]+)$", session_id, re.IGNORECASE) if session_id else None
    our_uuid = match.group(1) if match else None

    script = """
tell application "System Events"
    set frontApp to name of first application process whose frontmost is true
end tell
if frontApp is not "iTerm2" then
    return ""
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
    active_uuid = result.stdout.strip()

    if not active_uuid or not our_uuid:
        return True  # Can't determine, assume active (don't spam)
    return active_uuid.upper() == our_uuid.upper()


def notify(title: str, message: str, sound: str = "Glass") -> None:
    if is_active_tab():
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
        notify("Claude - Done", message)


if __name__ == "__main__":
    main()
