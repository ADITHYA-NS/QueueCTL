echo ""
echo "🧪 TEST SUITE: Edge Cases & Error Handling"
echo "==========================================="

# Test 7.1: Invalid Commands
echo "7.1 - Invalid Commands"
queuectl enqueue '{"id": "invalid_cmd", "command": "nonexistent_command_xyz123"}'

# Test 7.2: Long Running Commands
echo "7.2 - Long Running Commands"
queuectl enqueue '{"id": "long_cmd", "command": "sleep 10"}'

# Test 7.3: Command Timeout
echo "7.3 - Command Timeout"
queuectl enqueue '{"id": "timeout_test", "command": "sleep 30", "timeout": 5}'

# Test 7.4: Missing Job ID
echo "7.4 - Missing Job ID (API Level)"
curl -X POST "http://127.0.0.1:8000/enqueue" -H "Content-Type: application/json" -d '{"command": "echo test"}'

# Test 7.5: Invalid JSON
echo "7.5 - Invalid JSON Input"
queuectl enqueue 'invalid{json}'

# Test 7.6: Special Characters in Commands
echo "7.6 - Special Characters in Commands"
queuectl enqueue '{"id": "special_chars", "command": "echo \"Hello; World && ls || pwd\""}'

echo ""
echo "🧪 TEST SUITE: Performance & Scalability"
echo "========================================="

# Test 8.1: Multiple Rapid Job Submissions
echo "8.1 - Multiple Rapid Job Submissions"
for i in {1..20}; do
    queuectl enqueue "{\"id\": \"fast_$i\", \"command\": \"echo Quick Job $i\"}" &
done
wait

# Test 8.2: Concurrent Worker Processing
echo "8.2 - Concurrent Worker Processing"
queuectl worker start --count 5
sleep 8
queuectl status

# Test 8.3: Mixed Workload Types
echo "8.3 - Mixed Workload Types"
queuectl enqueue '{"id": "mixed1", "command": "echo instant"}'
queuectl enqueue '{"id": "mixed2", "command": "sleep 4"}'
queuectl enqueue '{"id": "mixed3", "command": "find . -name \"*.py\" | head -5"}'
queuectl enqueue '{"id": "mixed4", "command": "exit 1"}'

sleep 10
queuectl status

echo ""
echo "🧪 TEST SUITE: Integration & End-to-End"
echo "========================================"

# Test 9.1: Complete Workflow
echo "9.1 - Complete Workflow Test"
queuectl config set max_retries 3
queuectl config set base_delay 2

# Add various job types
queuectl enqueue '{"id": "workflow1", "command": "echo Success Job"}'
queuectl enqueue '{"id": "workflow2", "command": "sleep 3"}'
queuectl enqueue '{"id": "workflow3", "command": "exit 1"}'
queuectl enqueue '{"id": "workflow4", "command": "ls -la"}'

# Process them
queuectl worker start --count 3
sleep 15

# Check results
queuectl status
queuectl list --state completed
queuectl list --state failed
queuectl dlq list

# Test 9.2: DLQ Recovery Workflow
echo "9.2 - DLQ Recovery Workflow"
queuectl dlq retry workflow3
queuectl worker start --count 1
sleep 8
queuectl status

# Test 9.3: Configuration Impact
echo "9.3 - Configuration Impact Verification"
queuectl config get max_retries
queuectl config get base_delay

echo ""
echo "🧪 TEST SUITE: Data Persistence"
echo "================================"

# Test 10.1: Job Persistence Across Restarts
echo "10.1 - Job Persistence Across Restarts"
queuectl enqueue '{"id": "persist1", "command": "echo I survive restarts"}'
queuectl enqueue '{"id": "persist2", "command": "sleep 5"}'

# Simulate restart (stop workers, they should restart and continue)
queuectl worker stop
sleep 3
queuectl worker start --count 2
sleep 8

# Verify jobs were processed
queuectl list --state completed

# Test 10.2: Configuration Persistence
echo "10.2 - Configuration Persistence"
queuectl config set max_retries 4
# Restart backend server here manually, then:
queuectl config get max_retries  # Should still be 4

