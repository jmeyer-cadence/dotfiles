#!/usr/bin/env python3
"""Claude Code desktop notification hook.

Works for both Notification and Stop hook events.
Fires a macOS desktop notification via osascript.
"""

import json
import subprocess
import sys


def notify(title: str, message: str, sound: str = "Glass") -> None:
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
        notify("Claude - Done", message, sound="Glass")


if __name__ == "__main__":
    main()
