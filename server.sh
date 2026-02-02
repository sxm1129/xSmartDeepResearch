#!/bin/bash

# Configuration
BACKEND_PORT=8000
FRONTEND_PORT=3002
PYTHON_CMD="/opt/miniconda3/envs/deepresearch_env/bin/python"
PROJECT_ROOT=$(pwd)

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Helper Functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_port() {
    lsof -t -i:$1 > /dev/null
    return $?
}

kill_port() {
    local port=$1
    local pids=$(lsof -t -i:$port)
    if [ -n "$pids" ]; then
        log_warn "Killing process(es) on port $port: $pids"
        kill -9 $pids
    else
        log_info "No process found on port $port"
    fi
}

start_backend() {
    log_info "Starting Backend on port $BACKEND_PORT..."
    if check_port $BACKEND_PORT; then
        log_error "Port $BACKEND_PORT is already in use. Use 'restart' or 'stop' first."
        return 1
    fi
    
    nohup $PYTHON_CMD -m uvicorn src.api.main:app --host 0.0.0.0 --port $BACKEND_PORT > backend.log 2>&1 &
    echo $! > backend.pid
    log_info "Backend started (PID: $(cat backend.pid)). Logs: backend.log"
}

start_frontend() {
    log_info "Starting Frontend on port $FRONTEND_PORT..."
    if check_port $FRONTEND_PORT; then
        log_error "Port $FRONTEND_PORT is already in use. Use 'restart' or 'stop' first."
        return 1
    fi

    # Go to web dir
    cd $PROJECT_ROOT/web
    
    # Use 'npm run dev' but specifically pass the port. 
    # Note: 'npm run dev' usually runs vite which handles --port, but passing arguments to npm run requires --
    nohup npm run dev -- --port $FRONTEND_PORT > ../frontend.log 2>&1 &
    echo $! > ../frontend.pid
    
    # Go back
    cd $PROJECT_ROOT
    
    log_info "Frontend started (PID: $(cat frontend.pid)). Logs: frontend.log"
}

stop_backend() {
    log_info "Stopping Backend..."
    if [ -f backend.pid ]; then
        kill $(cat backend.pid) 2>/dev/null
        rm backend.pid
    fi
    kill_port $BACKEND_PORT
    log_info "Backend stopped."
}

stop_frontend() {
    log_info "Stopping Frontend..."
    if [ -f frontend.pid ]; then
        kill $(cat frontend.pid) 2>/dev/null
        rm frontend.pid
    fi
    kill_port $FRONTEND_PORT
    log_info "Frontend stopped."
}

status_service() {
    local service=$1
    local port=$2
    if check_port $port; then
        local pid=$(lsof -t -i:$port)
        log_info "$service is RUNNING (PID: $pid, Port: $port)"
    else
        log_warn "$service is STOPPED (Port: $port)"
    fi
}

# Main Logic
ACTION=$1
TARGET=$2

if [ -z "$ACTION" ]; then
    echo "Usage: $0 {start|stop|restart|status} {frontend|backend|all}"
    exit 1
fi

if [ -z "$TARGET" ]; then
    TARGET="all"
fi

case "$ACTION" in
    start)
        case "$TARGET" in
            backend) start_backend ;;
            frontend) start_frontend ;;
            all) start_backend; start_frontend ;;
            *) echo "Invalid target: $TARGET"; exit 1 ;;
        esac
        ;;
    stop)
        case "$TARGET" in
            backend) stop_backend ;;
            frontend) stop_frontend ;;
            all) stop_backend; stop_frontend ;;
            *) echo "Invalid target: $TARGET"; exit 1 ;;
        esac
        ;;
    restart)
        case "$TARGET" in
            backend) stop_backend; sleep 2; start_backend ;;
            frontend) stop_frontend; sleep 2; start_frontend ;;
            all) stop_backend; stop_frontend; sleep 2; start_backend; start_frontend ;;
            *) echo "Invalid target: $TARGET"; exit 1 ;;
        esac
        ;;
    status)
        case "$TARGET" in
            backend) status_service "Backend" $BACKEND_PORT ;;
            frontend) status_service "Frontend" $FRONTEND_PORT ;;
            all) status_service "Backend" $BACKEND_PORT; status_service "Frontend" $FRONTEND_PORT ;;
            *) echo "Invalid target: $TARGET"; exit 1 ;;
        esac
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status} {frontend|backend|all}"
        exit 1
        ;;
esac
