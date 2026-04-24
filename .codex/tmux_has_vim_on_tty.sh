#!/usr/bin/env bash

set -euo pipefail

tty_path=${1:-}
if [[ -z "$tty_path" ]]; then
  exit 2
fi

tty_name=${tty_path#/dev/}

ps -axo pgid=,tpgid=,tty=,comm= | awk -v tty="$tty_name" '
function basename(path, count, parts) {
  count = split(path, parts, "/")
  return parts[count]
}

$3 == tty && $1 == $2 {
  cmd = basename($4)
  if (cmd ~ /^(g?vim|nvim|vi|view|vimdiff|vimx|rvim|rview)$/) {
    found = 1
  }
}

END {
  exit found ? 0 : 1
}
'
