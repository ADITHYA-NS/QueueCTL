#!/bin/bash

echo "🚀 Quick Assignment Validation"
echo "==============================="

echo "1. Basic Job Management"
queuectl enqueue '{"id": "quick1", "command": "echo Quick Test"}'
queuectl list

echo "2. Worker Execution"
queuectl worker start --count 1
sleep 3
queuectl list --state completed

echo "3. Retry Mechanism"
queuectl enqueue '{"id": "quick_retry", "command": "exit 1"}'
sleep 8
queuectl dlq list

echo "4. Configuration"
queuectl config set max_retries 3
queuectl config get max_retries

echo "5. Final Status"
queuectl status

echo "✅ Quick validation completed"