#!/usr/bin/env python3
"""Claude Code desktop notification hook.

Works for both Notification and Stop hook events.
Sends notifications via iTerm2's escape sequence, which writes directly to
the TTY so macOS notification permissions are handled by iTerm2 itself.
"""

import json
import sys


def notify(title: str, message: str) -> None:
    # iTerm2 proprietary escape sequence: ESC ] 9 ; <message> BEL
    # Writing to /dev/tty bypasses any stdout redirection from the hook runner.
    text = f"{title}: {message}"
    try:
        with open("/dev/tty", "w") as tty:
            tty.write(f"\033]9;{text}\007")
    except OSError:
        pass


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

        notify(title, message)

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
