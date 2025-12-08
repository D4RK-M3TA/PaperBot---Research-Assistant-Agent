#!/bin/bash

# PaperBot Startup Script
# This script starts both the backend and frontend servers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directories
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_DIR"
FRONTEND_DIR="$PROJECT_DIR/frontend"
VENV_DIR="$PROJECT_DIR/venv"

# Log files
BACKEND_LOG="/tmp/paperbot_backend.log"
FRONTEND_LOG="/tmp/paperbot_frontend.log"

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

# Function to check if a port is in use
check_port() {
    local port=$1
    # Try multiple methods to check if port is in use
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    elif ss -tlnp 2>/dev/null | grep -q ":$port "; then
        return 0  # Port is in use
    elif netstat -tln 2>/dev/null | grep -q ":$port "; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill process on a port
kill_port() {
    local port=$1
    print_info "Checking port $port..."
    if check_port $port; then
        print_warning "Port $port is in use. Attempting to free it..."
        lsof -ti:$port 2>/dev/null | xargs kill -9 2>/dev/null || true
        fuser -k $port/tcp 2>/dev/null || true
        sleep 2
        if check_port $port; then
            print_error "Could not free port $port. Please stop the application using it manually."
            return 1
        else
            print_success "Port $port is now free"
        fi
    else
        print_success "Port $port is available"
    fi
    return 0
}

# Function to check if virtual environment exists
check_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        print_error "Virtual environment not found at $VENV_DIR"
        print_info "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
        print_success "Virtual environment created"
    fi
}

# Function to activate virtual environment
activate_venv() {
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
        print_success "Virtual environment activated"
    else
        print_error "Could not activate virtual environment"
        exit 1
    fi
}

# Function to check if dependencies are installed
check_dependencies() {
    print_info "Checking backend dependencies..."
    if ! python -c "import django" 2>/dev/null; then
        print_warning "Django not found. Installing dependencies..."
        pip install -q -r requirements.txt
        print_success "Backend dependencies installed"
    fi
    
    print_info "Checking frontend dependencies..."
    if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        print_warning "Frontend node_modules not found. Installing dependencies..."
        cd "$FRONTEND_DIR"
        npm install
        cd "$PROJECT_DIR"
        print_success "Frontend dependencies installed"
    fi
}

# Function to start backend
start_backend() {
    print_info "Starting Django backend server..."
    cd "$BACKEND_DIR"
    
    # Check if database needs migration
    if [ ! -f "db.sqlite3" ] || [ "manage.py" -nt "db.sqlite3" ]; then
        print_info "Running database migrations..."
        python manage.py migrate --noinput >/dev/null 2>&1 || true
    fi
    
    # Start backend with environment variable
    export USE_SQLITE=True
    python manage.py runserver 8000 > "$BACKEND_LOG" 2>&1 &
    BACKEND_PID=$!
    unset USE_SQLITE
    
    # Wait and check if it started successfully (with retries)
    local max_attempts=10
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        sleep 1
        if check_port 8000; then
            print_success "Backend started on http://localhost:8000 (PID: $BACKEND_PID)"
            echo $BACKEND_PID > /tmp/paperbot_backend.pid
            return 0
        fi
        attempt=$((attempt + 1))
    done
    
    # Check if process is still running (might have crashed)
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        print_error "Backend process crashed. Check $BACKEND_LOG for details:"
        tail -20 "$BACKEND_LOG"
        return 1
    fi
    
    # Process is running but port check failed - might be a timing issue
    print_warning "Backend process is running (PID: $BACKEND_PID) but port check failed."
    print_info "Checking log for errors..."
    if grep -i "error\|exception\|traceback" "$BACKEND_LOG" >/dev/null 2>&1; then
        print_error "Errors found in backend log:"
        tail -20 "$BACKEND_LOG"
        return 1
    else
        print_success "Backend appears to be starting (PID: $BACKEND_PID)"
        echo $BACKEND_PID > /tmp/paperbot_backend.pid
        return 0
    fi
}

# Function to start frontend
start_frontend() {
    print_info "Starting Vite frontend server..."
    cd "$FRONTEND_DIR"
    
    # Start frontend
    npm run dev > "$FRONTEND_LOG" 2>&1 &
    FRONTEND_PID=$!
    
    # Wait and check if it started successfully (with retries)
    local max_attempts=15
    local attempt=0
    local frontend_port=""
    
    while [ $attempt -lt $max_attempts ]; do
        sleep 1
        if check_port 3000; then
            frontend_port=3000
            break
        elif check_port 3001; then
            frontend_port=3001
            break
        fi
        attempt=$((attempt + 1))
    done
    
    if [ -n "$frontend_port" ]; then
        if [ "$frontend_port" = "3001" ]; then
            print_warning "Frontend started on http://localhost:3001 (port 3000 was in use) (PID: $FRONTEND_PID)"
        else
            print_success "Frontend started on http://localhost:3000 (PID: $FRONTEND_PID)"
        fi
        echo $FRONTEND_PID > /tmp/paperbot_frontend.pid
        return 0
    fi
    
    # Check if process is still running
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        print_error "Frontend process crashed. Check $FRONTEND_LOG for details:"
        tail -20 "$FRONTEND_LOG"
        return 1
    fi
    
    # Process is running but port check failed
    print_warning "Frontend process is running (PID: $FRONTEND_PID) but port check failed."
    print_info "Checking log for errors..."
    if grep -i "error\|exception\|failed" "$FRONTEND_LOG" >/dev/null 2>&1; then
        print_error "Errors found in frontend log:"
        tail -20 "$FRONTEND_LOG"
        return 1
    else
        print_success "Frontend appears to be starting (PID: $FRONTEND_PID)"
        echo $FRONTEND_PID > /tmp/paperbot_frontend.pid
        return 0
    fi
}

# Function to stop servers
stop_servers() {
    print_info "Stopping servers..."
    
    # Stop by PID file
    if [ -f /tmp/paperbot_backend.pid ]; then
        BACKEND_PID=$(cat /tmp/paperbot_backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID 2>/dev/null || true
            sleep 1
            kill -9 $BACKEND_PID 2>/dev/null || true
            print_success "Backend stopped (PID: $BACKEND_PID)"
        fi
        rm -f /tmp/paperbot_backend.pid
    fi
    
    if [ -f /tmp/paperbot_frontend.pid ]; then
        FRONTEND_PID=$(cat /tmp/paperbot_frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID 2>/dev/null || true
            sleep 1
            kill -9 $FRONTEND_PID 2>/dev/null || true
            print_success "Frontend stopped (PID: $FRONTEND_PID)"
        fi
        rm -f /tmp/paperbot_frontend.pid
    fi
    
    # Also kill any processes on the ports (more thorough)
    for port in 8000 3000 3001; do
        PIDS=$(lsof -ti:$port 2>/dev/null || true)
        if [ -n "$PIDS" ]; then
            echo "$PIDS" | xargs kill -9 2>/dev/null || true
        fi
    done
    
    sleep 1
    print_success "All servers stopped"
}

# Function to show status
show_status() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📋 PaperBot Status"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    if check_port 8000; then
        print_success "Backend:  http://localhost:8000"
    else
        print_error "Backend:  Not running"
    fi
    
    if check_port 3000; then
        print_success "Frontend: http://localhost:3000"
    elif check_port 3001; then
        print_success "Frontend: http://localhost:3001"
    else
        print_error "Frontend: Not running"
    fi
    
    echo ""
    echo "Log files:"
    echo "  Backend:  $BACKEND_LOG"
    echo "  Frontend: $FRONTEND_LOG"
    echo ""
}

# Trap to handle script interruption
trap 'echo ""; print_warning "Interrupted. Use ./start.sh stop to stop servers."; exit 1' INT TERM

# Main execution
main() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🚀 Starting PaperBot"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Handle stop command
    if [ "$1" == "stop" ]; then
        stop_servers
        exit 0
    fi
    
    # Handle status command
    if [ "$1" == "status" ]; then
        show_status
        exit 0
    fi
    
    # Check if already running
    if check_port 8000 || check_port 3000 || check_port 3001; then
        print_warning "Servers appear to be already running."
        read -p "Do you want to restart them? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            stop_servers
            sleep 2
        else
            show_status
            exit 0
        fi
    fi
    
    # Setup
    check_venv
    activate_venv
    check_dependencies
    
    # Free ports
    kill_port 8000 || exit 1
    kill_port 3000 || print_warning "Could not free port 3000, will try 3001"
    
    # Start servers
    start_backend || exit 1
    start_frontend || (stop_servers && exit 1)
    
    # Show status
    show_status
    
    echo ""
    print_success "PaperBot is running!"
    echo ""
    echo "To stop the servers, run: ./start.sh stop"
    echo "To check status, run: ./start.sh status"
    echo ""
    echo "Press Ctrl+C to exit (servers will continue running in background)"
    echo ""
    
    # Keep script running
    wait
}

# Run main function
main "$@"


