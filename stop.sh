#!/bin/bash

# Agentic Drop Zone - Clean Stop Script
# This script ensures all processes are properly terminated

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PIDFILE="agentic_drop_zone.pid"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to kill processes on port
kill_port() {
    local port=$1
    local pids=$(lsof -ti:$port 2>/dev/null || true)
    if [ -n "$pids" ]; then
        print_warning "Killing processes on port $port: $pids"
        echo $pids | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

print_status "Stopping Agentic Drop Zone..."

# Stop main process if PID file exists
if [ -f "$PIDFILE" ]; then
    pid=$(cat "$PIDFILE" 2>/dev/null || echo "")
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        print_status "Stopping process $pid..."
        kill -TERM "$pid" 2>/dev/null || true

        # Wait for graceful shutdown
        count=0
        while [ $count -lt 10 ] && kill -0 "$pid" 2>/dev/null; do
            sleep 1
            count=$((count + 1))
            echo -n "."
        done
        echo ""

        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            print_warning "Force killing process $pid..."
            kill -KILL "$pid" 2>/dev/null || true
        fi

        print_status "Process $pid stopped"
    else
        print_warning "Process not running (PID file exists but process not found)"
    fi
    rm -f "$PIDFILE"
else
    print_status "No PID file found"
fi

# Clean up any remaining processes
print_status "Cleaning up any remaining processes..."
pkill -f "sfs_agentic_drop_zone.py" 2>/dev/null && print_status "Killed remaining python processes" || true
pkill -f "uv run sfs_agentic_drop_zone.py" 2>/dev/null && print_status "Killed remaining uv processes" || true

# Clean up ports
DEFAULT_PORT=8080
HEALTH_SERVER_PORT=${HEALTH_SERVER_PORT:-$DEFAULT_PORT}
kill_port $HEALTH_SERVER_PORT
kill_port 8081  # Also check alternate port

print_status "All processes stopped and ports freed"
print_status "✅ Agentic Drop Zone shutdown complete"