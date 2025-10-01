#!/bin/bash

# Agentic Drop Zone - Clean Startup Script
# This script ensures clean startup and provides proper shutdown mechanisms

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
DEFAULT_PORT=8080
HEALTH_SERVER_PORT=${HEALTH_SERVER_PORT:-$DEFAULT_PORT}
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

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1  # Port is in use
    else
        return 0  # Port is available
    fi
}

# Function to kill processes on port
kill_port() {
    local port=$1
    local pids=$(lsof -ti:$port 2>/dev/null || true)
    if [ -n "$pids" ]; then
        print_warning "Killing processes on port $port: $pids"
        echo $pids | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# Function to cleanup on exit
cleanup() {
    print_status "Shutting down Agentic Drop Zone..."

    # Kill the main process if PID file exists
    if [ -f "$PIDFILE" ]; then
        local pid=$(cat "$PIDFILE" 2>/dev/null || echo "")
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            print_status "Stopping process $pid..."
            kill -TERM "$pid" 2>/dev/null || true

            # Wait for graceful shutdown
            local count=0
            while [ $count -lt 10 ] && kill -0 "$pid" 2>/dev/null; do
                sleep 1
                count=$((count + 1))
            done

            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                print_warning "Force killing process $pid..."
                kill -KILL "$pid" 2>/dev/null || true
            fi
        fi
        rm -f "$PIDFILE"
    fi

    # Clean up any remaining processes
    pkill -f "sfs_agentic_drop_zone.py" 2>/dev/null || true

    # Clean up ports
    kill_port $HEALTH_SERVER_PORT

    print_status "Cleanup completed"
}

# Function to start the application
start_app() {
    print_header "═══════════════════════════════════════"
    print_header "      🚀 Starting Agentic Drop Zone"
    print_header "═══════════════════════════════════════"

    # Check if port is available
    if ! check_port $HEALTH_SERVER_PORT; then
        print_error "Port $HEALTH_SERVER_PORT is already in use!"
        print_status "Attempting to free port $HEALTH_SERVER_PORT..."
        kill_port $HEALTH_SERVER_PORT
        sleep 2

        if ! check_port $HEALTH_SERVER_PORT; then
            print_error "Unable to free port $HEALTH_SERVER_PORT. Exiting."
            exit 1
        fi
    fi

    print_status "Port $HEALTH_SERVER_PORT is available"

    # Check for existing PID file
    if [ -f "$PIDFILE" ]; then
        local old_pid=$(cat "$PIDFILE" 2>/dev/null || echo "")
        if [ -n "$old_pid" ] && kill -0 "$old_pid" 2>/dev/null; then
            print_error "Agentic Drop Zone is already running (PID: $old_pid)"
            print_status "Use './stop.sh' to stop the existing instance first"
            exit 1
        else
            print_warning "Removing stale PID file"
            rm -f "$PIDFILE"
        fi
    fi

    # Start the application
    print_status "Starting Agentic Drop Zone on port $HEALTH_SERVER_PORT..."

    # Set up signal handlers for cleanup
    trap cleanup EXIT INT TERM

    # Run the application and capture PID
    HEALTH_SERVER_PORT=$HEALTH_SERVER_PORT uv run sfs_agentic_drop_zone.py &
    local app_pid=$!
    echo $app_pid > "$PIDFILE"

    print_status "Started with PID: $app_pid"
    print_status "Health server will be available at: http://127.0.0.1:$HEALTH_SERVER_PORT/health"
    print_status "Press Ctrl+C to stop gracefully"

    # Wait for the process
    wait $app_pid
}

# Main execution
case "${1:-start}" in
    "start")
        start_app
        ;;
    "stop")
        cleanup
        ;;
    "restart")
        cleanup
        sleep 2
        start_app
        ;;
    "status")
        if [ -f "$PIDFILE" ]; then
            local pid=$(cat "$PIDFILE" 2>/dev/null || echo "")
            if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
                print_status "Agentic Drop Zone is running (PID: $pid)"
                if check_port $HEALTH_SERVER_PORT; then
                    print_warning "Health server port $HEALTH_SERVER_PORT is not listening"
                else
                    print_status "Health server is available at http://127.0.0.1:$HEALTH_SERVER_PORT/health"
                fi
            else
                print_status "Agentic Drop Zone is not running (stale PID file)"
                rm -f "$PIDFILE"
            fi
        else
            print_status "Agentic Drop Zone is not running"
        fi
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 {start|stop|restart|status|help}"
        echo ""
        echo "Commands:"
        echo "  start    - Start Agentic Drop Zone (default)"
        echo "  stop     - Stop Agentic Drop Zone"
        echo "  restart  - Restart Agentic Drop Zone"
        echo "  status   - Check if Agentic Drop Zone is running"
        echo "  help     - Show this help message"
        echo ""
        echo "Environment Variables:"
        echo "  HEALTH_SERVER_PORT  - Port for health server (default: 8080)"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac