#!/usr/bin/env bash
set -euo pipefail
unset CLAUDECODE 2>/dev/null || true

# --- Arguments ---
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
ROLE="${1:?ERROR: Role required (strategist|critic)}"
GOAL="${2:?ERROR: Goal text or @filepath required}"
SESSION_ID="${3:-$(date +%s)}"
PROJECT_DIR="${4:-$(pwd)}"

# --- Handle @filepath goals ---
if [[ "$GOAL" == @* ]]; then
    GOAL_PATH="${GOAL#@}"
    # Resolve relative to PROJECT_DIR
    if [[ ! "$GOAL_PATH" = /* ]] && [[ ! "$GOAL_PATH" =~ ^[A-Za-z]: ]]; then
        GOAL_PATH="$PROJECT_DIR/$GOAL_PATH"
    fi
    [[ -f "$GOAL_PATH" ]] || { echo "ERROR: Goal file not found: $GOAL_PATH" >&2; exit 1; }
    GOAL=$(cat "$GOAL_PATH")
fi

# --- Defaults (no config file needed) ---
MODEL="opus"
FALLBACK="sonnet"
MAX_TURNS=5
MAX_BUDGET="2.00"

# --- Optional config override ---
CONFIG_FILE="$PROJECT_DIR/.council/config.yaml"
if [[ -f "$CONFIG_FILE" ]]; then
    _MODEL=$(grep -A1 "^model:" "$CONFIG_FILE" 2>/dev/null | grep "default:" | awk '{print $2}')
    [[ -n "${_MODEL:-}" ]] && MODEL="$_MODEL"
    _FALLBACK=$(grep -A2 "^model:" "$CONFIG_FILE" 2>/dev/null | grep "fallback:" | awk '{print $2}')
    [[ -n "${_FALLBACK:-}" ]] && FALLBACK="$_FALLBACK"
    _TURNS=$(grep -A1 "^limits:" "$CONFIG_FILE" 2>/dev/null | grep "max_turns:" | awk '{print $2}')
    [[ -n "${_TURNS:-}" ]] && MAX_TURNS="$_TURNS"
    _BUDGET=$(grep -A2 "^limits:" "$CONFIG_FILE" 2>/dev/null | grep "max_budget_usd:" | awk '{print $2}')
    [[ -n "${_BUDGET:-}" ]] && MAX_BUDGET="$_BUDGET"
fi

# --- Paths ---
AGENT_DEF="$PLUGIN_ROOT/agents/${ROLE}.md"
MEMORY_LOG="$PROJECT_DIR/.council/memory/${ROLE}-log.md"
MEMORY_ACTIVE="$PROJECT_DIR/.council/memory/${ROLE}-active.md"
OUTPUT_FILE="$PROJECT_DIR/.council/bus/satellites/${SESSION_ID}-${ROLE}.md"
LOG_FILE="$PROJECT_DIR/.council/logs/${SESSION_ID}-${ROLE}.log"

# Use workspace dir for temp files (Windows /tmp/ is unreliable for claude -p subprocesses)
TEMP_DIR="$PROJECT_DIR/.council/.tmp"
mkdir -p "$TEMP_DIR"
SYSTEM_FILE="$TEMP_DIR/system-${ROLE}-${SESSION_ID}.md"
GOAL_FILE="$TEMP_DIR/goal-${ROLE}-${SESSION_ID}.md"

# Validate
[[ -f "$AGENT_DEF" ]] || { echo "ERROR: Agent definition not found: $AGENT_DEF" >&2; exit 1; }

# Defensive dir creation
mkdir -p "$PROJECT_DIR/.council/bus/satellites" "$PROJECT_DIR/.council/logs" "$PROJECT_DIR/.council/memory"

# --- Build system prompt ---
{
    cat "$AGENT_DEF"
    echo ""
    echo "---"
    echo ""
    echo "## Your Persistent Memory"
    echo ""
    if [[ -f "$MEMORY_ACTIVE" ]]; then
        cat "$MEMORY_ACTIVE"
    elif [[ -f "$MEMORY_LOG" ]]; then
        echo "*No compacted memory yet. Full log:*"
        cat "$MEMORY_LOG"
    else
        echo "*No prior memory.*"
    fi
    echo ""
    echo "---"
    echo ""
    echo "## Output Instructions"
    echo ""
    echo "Write your complete analysis to: \`$OUTPUT_FILE\`"
    echo "Use the Write tool to create this file. 300-500 words. Start with your recommendation."
} > "$SYSTEM_FILE"

# --- Goal as user message (stdin) ---
echo "$GOAL" > "$GOAL_FILE"

# --- Launch satellite ---
cd "$PROJECT_DIR" && claude -p \
    --model "$MODEL" \
    --fallback-model "$FALLBACK" \
    --append-system-prompt-file "$SYSTEM_FILE" \
    --disallowedTools "Task,WebFetch,WebSearch,NotebookEdit" \
    --allowedTools "Read,Write,Glob,Grep,Bash" \
    --max-turns "$MAX_TURNS" \
    --max-budget-usd "$MAX_BUDGET" \
    --no-session-persistence \
    --output-format stream-json \
    < "$GOAL_FILE" \
    > "$LOG_FILE" 2>&1

EXIT_CODE=$?

# Cleanup temp files
rm -f "$SYSTEM_FILE" "$GOAL_FILE"
rmdir "$TEMP_DIR" 2>/dev/null || true

# Check exit
if (( EXIT_CODE != 0 )); then
    echo "ERROR: $ROLE satellite failed (exit $EXIT_CODE). Check $LOG_FILE" >&2
    exit "$EXIT_CODE"
fi

# Validate output was written
if [[ ! -f "$OUTPUT_FILE" ]]; then
    echo "ERROR: $ROLE exited 0 but output file not created: $OUTPUT_FILE" >&2
    echo "Check $LOG_FILE for details" >&2
    exit 1
fi

echo "OK: $ROLE completed -> $OUTPUT_FILE"
