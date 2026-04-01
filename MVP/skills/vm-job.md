---
name: vm-job
description: Launch and monitor long-running jobs on a GPU VM — sets up tmux session, runs with nohup, writes status file, tails log. Handles subagent permission failures gracefully.
---

# VM Job

Launch a long-running job on a local or remote GPU VM with proper session management so it survives disconnects and can be monitored.

## Step 0 — Identify the job

Confirm with user:
- The script/command to run
- Expected duration
- Output directory
- Whether running locally or on a remote VM (if remote, confirm SSH access)

## Step 1 — Pre-flight check

```bash
# Check GPU availability
nvidia-smi 2>/dev/null || echo "No NVIDIA GPU found"

# Check Ollama if needed
curl -s http://localhost:11434/api/tags 2>/dev/null | python3 -m json.tool 2>/dev/null | head -20 || echo "Ollama not running"

# Disk space
df -h . | tail -1

# Check if tmux available
which tmux && tmux -V || echo "tmux not available — will use nohup"
```

## Step 2 — Launch with tmux (preferred)

If tmux is available:

```bash
SESSION="job_$(date +%Y%m%d_%H%M%S)"
LOG="logs/${SESSION}.log"
STATUS="logs/${SESSION}.status"

mkdir -p logs

# Create status file
echo "STARTED: $(date)" > "$STATUS"
echo "COMMAND: <command>" >> "$STATUS"

# Launch in tmux
tmux new-session -d -s "$SESSION" \
  "python <script.py> <args> 2>&1 | tee $LOG; echo 'EXIT: '$? >> $STATUS; echo 'DONE: '$(date) >> $STATUS"

echo "Session: $SESSION"
echo "Log: $LOG"
echo "Status: $STATUS"
echo ""
echo "Monitor with: tmux attach -t $SESSION"
echo "Or tail log:  tail -f $LOG"
```

## Step 2b — Launch with nohup (fallback)

If tmux is not available or subagents lack permissions:

```bash
LOG="logs/job_$(date +%Y%m%d_%H%M%S).log"
STATUS="${LOG%.log}.status"

mkdir -p logs
echo "STARTED: $(date)" > "$STATUS"

nohup python <script.py> <args> > "$LOG" 2>&1 &
PID=$!
echo "PID: $PID" >> "$STATUS"

echo "Job launched with PID: $PID"
echo "Log: $LOG"
echo "Monitor: tail -f $LOG"
echo "Check alive: ps -p $PID"
```

## Step 3 — Monitor progress

```bash
# Tail the log
tail -f "$LOG"
```

Check for common progress patterns:
```bash
# Count processed items (adjust pattern to match your script's output)
grep -c "processed\|completed\|done" "$LOG" 2>/dev/null
tail -5 "$LOG"
cat "$STATUS"
```

## Step 4 — Status summary

Report to user:
- Job running: yes/no (PID alive or tmux session active)
- Items processed (from log grep)
- Any errors in log
- Estimated completion (if log shows rate)
- How to re-attach or check later

If job has already failed, show last 20 lines of log and suggest diagnosis with `/investigate`.
