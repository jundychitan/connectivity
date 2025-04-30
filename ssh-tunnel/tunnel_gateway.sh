#!/bin/bash

# Define the tunnel pattern to search for
TUNNEL_PATTERN="ssh -o StrictHostKeyChecking=no -N -R 0.0.0.0:2022:localhost:22 root@139.162.31.224"

# Check if the tunnel is already running
if pgrep -f "$TUNNEL_PATTERN" > /dev/null; then
    echo "Tunnel is already running."
else
    echo "Starting SSH tunnel..."
    ssh -o StrictHostKeyChecking=no -N -R 0.0.0.0:2022:localhost:22 root@139.162.31.224 &
    echo $! > /tmp/tunnel_gateway.pid
    echo "Tunnel started with PID $(cat /tmp/tunnel_gateway.pid)"
fi

