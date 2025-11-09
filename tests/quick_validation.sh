#!/bin/bash

echo "🚀 Quick Assignment Validation"
echo "==============================="

echo "1. Basic Job Management"
echo "queuectl enqueue '{"id": "quick1", "command": "echo Quick Test"}'"
queuectl enqueue '{"id": "quick1", "command": "echo Quick Test"}'
queuectl list

echo "2. Worker Execution"
echo "queuectl worker start --count 1"
queuectl worker start --count 1
sleep 3
echo "queuectl list --state completed"
queuectl list --state completed

echo "3. Retry Mechanism"
echo "queuectl enqueue '{"id": "quick_retry", "command": "exit 1"}'"
queuectl enqueue '{"id": "quick_retry", "command": "exit 1"}'
sleep 8
echo "queuectl dlq list"
queuectl dlq list

echo "4. Configuration"
echo "queuectl config set max_retries 3"
queuectl config set max_retries 3
echo "queuectl config get max_retries"
queuectl config get max_retries

echo "5. Final Status"
echo "queuectl status"
queuectl status

echo "✅ Quick validation completed"