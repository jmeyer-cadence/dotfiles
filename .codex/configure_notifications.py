#!/usr/bin/env python3
"""Ensure Codex notification settings exist in config.toml."""

from __future__ import annotations

import pathlib
import re
import sys


NOTIFY_LINE = (
    'notify = ["sh", "-lc", "python3 \\"$HOME/.codex/notify.py\\" \\"$1\\"", "codex-notify"]'
)
TUI_LINES = [
    'notifications = ["approval-requested", "user-input-requested"]',
    'notification_method = "auto"',
]


def split_sections(content: str) -> tuple[list[str], list[tuple[str, list[str]]]]:
    prelude: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    current_header: str | None = None
    current_lines: list[str] = []

    for line in content.splitlines():
        if re.match(r"^\[[^\]]+\]\s*$", line):
            if current_header is None:
                prelude = current_lines
            else:
                sections.append((current_header, current_lines))
            current_header = line
            current_lines = []
            continue
        current_lines.append(line)

    if current_header is None:
        prelude = current_lines
    else:
        sections.append((current_header, current_lines))

    return prelude, sections


def ensure_notify(prelude: list[str]) -> list[str]:
    filtered = [line for line in prelude if not re.match(r"^\s*notify\s*=", line)]

    while filtered and filtered[-1] == "":
        filtered.pop()

    if filtered:
        filtered.append("")
    filtered.append(NOTIFY_LINE)
    return filtered


def ensure_tui_section(sections: list[tuple[str, list[str]]]) -> list[tuple[str, list[str]]]:
    updated: list[tuple[str, list[str]]] = []
    found = False

    for header, body in sections:
        if header != "[tui]":
            updated.append((header, body))
            continue

        found = True
        filtered = [
            line
            for line in body
            if not re.match(r"^\s*(notifications|notification_method)\s*=", line)
        ]
        while filtered and filtered[-1] == "":
            filtered.pop()
        if filtered:
            filtered.append("")
        filtered.extend(TUI_LINES)
        updated.append((header, filtered))

    if not found:
        updated.append(("[tui]", TUI_LINES.copy()))

    return updated


def render(prelude: list[str], sections: list[tuple[str, list[str]]]) -> str:
    blocks: list[str] = []

    if prelude:
        normalized_prelude = prelude[:]
        while normalized_prelude and normalized_prelude[-1] == "":
            normalized_prelude.pop()
        blocks.append("\n".join(normalized_prelude))

    for header, body in sections:
        normalized_body = body[:]
        while normalized_body and normalized_body[-1] == "":
            normalized_body.pop()
        if normalized_body:
            blocks.append("\n".join([header, *normalized_body]))
        else:
            blocks.append(header)

    return "\n\n".join(blocks).rstrip() + "\n"


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: configure_notifications.py <config-path>", file=sys.stderr)
        return 1

    path = pathlib.Path(sys.argv[1]).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    content = path.read_text() if path.exists() else ""

    prelude, sections = split_sections(content)
    prelude = ensure_notify(prelude)
    sections = ensure_tui_section(sections)

    path.write_text(render(prelude, sections))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
