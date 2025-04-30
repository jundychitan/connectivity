#!/bin/bash

PATTERN="ssh -o StrictHostKeyChecking=no -N -R 0.0.0.0:2022:localhost:22 root@139.162.31.224"

if pgrep -f "$PATTERN" > /dev/null; then
    pkill -f "$PATTERN"
    echo "Killed tunnel matching pattern: $PATTERN"
fi

