#!/usr/bin/env python3
"""Restore the relevant iTerm/tmux context when a Codex notification is clicked."""

import argparse
import base64
import json
import os
import re
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
ITERM_SESSION_PATTERN = re.compile(r"^w(\d+)t(\d+)p\d+:[A-F0-9-]+$", re.IGNORECASE)


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True)


def parse_iterm_session_id(session_id: Optional[str]) -> Optional[tuple[int, int]]:
    if not session_id:
        return None

    match = ITERM_SESSION_PATTERN.match(session_id)
    if not match:
        return None

    window_index = int(match.group(1)) + 1
    tab_index = int(match.group(2)) + 1
    return window_index, tab_index


def decode_context(encoded_context: Optional[str]) -> dict[str, str]:
    if not encoded_context:
        return {}

    try:
        payload = base64.urlsafe_b64decode(encoded_context.encode("ascii"))
        decoded = json.loads(payload.decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return {}

    if not isinstance(decoded, dict):
        return {}

    context: dict[str, str] = {}
    for key, value in decoded.items():
        if isinstance(value, str) and value:
            context[key] = value
    return context


def focus_iterm_tab(session_id: Optional[str]) -> bool:
    parsed = parse_iterm_session_id(session_id)
    if not parsed:
        return False

    window_index, tab_index = parsed
    script = f"""
tell application "iTerm2"
    if (count of windows) < {window_index} then
        return ""
    end if

    tell item {window_index} of windows
        select
        if (count of tabs) < {tab_index} then
            return ""
        end if
        tell item {tab_index} of tabs
            select
        end tell
    end tell

    activate
    return "focused"
end tell
"""
    result = run([OSASCRIPT, "-e", script])
    return result.returncode == 0 and result.stdout.strip() == "focused"


def focus_iterm_client(client_tty: Optional[str]) -> bool:
    if not client_tty:
        return False

    script = f"""
tell application "iTerm2"
    repeat with w in windows
        repeat with t in tabs of w
            repeat with s in sessions of t
                if tty of s is "{client_tty}" then
                    tell w to select
                    tell t to select
                    activate
                    return "focused"
                end if
            end repeat
        end repeat
    end repeat
end tell
"""
    result = run([OSASCRIPT, "-e", script])
    return result.returncode == 0 and result.stdout.strip() == "focused"


def focus_iterm_uuid(session_uuid: Optional[str]) -> bool:
    if session_uuid:
        script = f"""
tell application "iTerm2"
    repeat with w in windows
        repeat with t in tabs of w
            repeat with s in sessions of t
                if unique ID of s is "{session_uuid}" then
                    tell w to select
                    tell t to select
                    activate
                    return "focused"
                end if
            end repeat
        end repeat
    end repeat
end tell
"""
        result = run([OSASCRIPT, "-e", script])
        if result.returncode == 0 and result.stdout.strip() == "focused":
            return True

    return False


def focus_iterm_session(
    session_id: Optional[str],
    session_uuid: Optional[str],
    client_tty: Optional[str],
) -> None:
    # tmux panes retain the iTerm session env from when the pane was created,
    # so restore the visible tab from the attached tmux client tty first.
    if focus_iterm_client(client_tty):
        return

    if focus_iterm_uuid(session_uuid):
        return

    if focus_iterm_tab(session_id):
        return

    run([OSASCRIPT, "-e", 'tell application "iTerm2" to activate'])


def tmux_value(target: str, fmt: str) -> Optional[str]:
    result = run([TMUX, "display-message", "-p", "-t", target, fmt])
    if result.returncode != 0:
        return None

    value = result.stdout.strip()
    return value if value else None


def client_ttys_for_session(session_name: Optional[str]) -> list[str]:
    if not session_name:
        return []

    result = run([TMUX, "list-clients", "-F", "#{client_tty}\t#{session_name}"])
    if result.returncode != 0:
        return []

    client_ttys: list[str] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        client_tty, _, attached_session = line.partition("\t")
        if attached_session == session_name and client_tty:
            client_ttys.append(client_tty)
    return client_ttys


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


def select_tmux_pane(target: str) -> bool:
    return run([TMUX, "select-pane", "-t", target]).returncode == 0


def resolve_target_client(client_tty: Optional[str], session_name: Optional[str]) -> Optional[str]:
    if client_exists(client_tty):
        return client_tty

    client_ttys = client_ttys_for_session(session_name)
    if len(client_ttys) == 1:
        return client_ttys[0]

    return None


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
    target_client = resolve_target_client(client_tty, target_session)
    if not target_client or not target_session:
        return

    if not switch_tmux_client(target_client, target_session):
        return

    if target_window and target_exists(target_window):
        select_tmux_window(target_window)

    if pane_id and target_exists(pane_id):
        select_tmux_pane(pane_id)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--context")
    parser.add_argument("--iterm-session-id")
    parser.add_argument("--iterm-session")
    parser.add_argument("--client-tty")
    parser.add_argument("--session-name")
    parser.add_argument("--window-id")
    parser.add_argument("--pane-id")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    context = decode_context(args.context)

    iterm_session_id = args.iterm_session_id or context.get("iterm_session_id")
    iterm_session = args.iterm_session or context.get("iterm_session")
    client_tty = args.client_tty or context.get("client_tty")
    session_name = args.session_name or context.get("session_name")
    window_id = args.window_id or context.get("window_id")
    pane_id = args.pane_id or context.get("pane_id")

    focus_iterm_session(iterm_session_id, iterm_session, client_tty)
    focus_tmux_target(pane_id, window_id, session_name, client_tty)


if __name__ == "__main__":
    main()
