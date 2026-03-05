#!/bin/bash

DIRECTION=$1

IFS=', ' read -r x1 y1 x2 y2 <<< "$(osascript -e 'tell application "Finder" to get bounds of window of desktop')"
W=$((x2 - x1))
H=$((y2 - y1))

case "$DIRECTION" in
    left)     POS_X=$x1;           POS_Y=$y1; SIZE_W=$((W/2)); SIZE_H=$H ;;
    right)    POS_X=$((x1 + W/2)); POS_Y=$y1; SIZE_W=$((W/2)); SIZE_H=$H ;;
    maximize) POS_X=$x1;           POS_Y=$y1; SIZE_W=$W;        SIZE_H=$H ;;
    *) echo "Usage: $0 left|right|maximize" >&2; exit 1 ;;
esac

osascript -e "
tell application \"System Events\"
    set frontApp to first application process whose frontmost is true
    set position of first window of frontApp to {$POS_X, $POS_Y}
    set size of first window of frontApp to {$SIZE_W, $SIZE_H}
end tell
"
