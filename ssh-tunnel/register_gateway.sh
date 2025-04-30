#!/bin/bash

# Variables
KEY_PATH="$HOME/.ssh/id_rsa"
PUB_KEY_PATH="${KEY_PATH}.pub"
API_URL="http://139.162.31.224:8000/register"  # Replace with your actual server endpoint

# 1. Generate SSH key if it doesn't exist
if [ ! -f "$PUB_KEY_PATH" ]; then
    echo "Generating SSH key..."
    ssh-keygen -t rsa -b 4096 -f "$KEY_PATH" -N ""
else
    echo "SSH key already exists at $PUB_KEY_PATH"
fi

# 2. Read public key
SSH_KEY=$(cat "$PUB_KEY_PATH")

# 3. Get hostname
HOSTNAME=$(hostname)

# 4. Send to REST API
echo "Sending public key to server..."
curl -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -d "{\"hostname\":\"$HOSTNAME\", \"ssh_key\":\"$SSH_KEY\"}"

