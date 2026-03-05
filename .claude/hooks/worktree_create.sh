#!/usr/bin/env bash
set -euo pipefail

NAME=$(jq -r .name)
DIR="$(dirname "$(git rev-parse --show-toplevel)")/$NAME"
git worktree add "$DIR"
echo "$DIR"
