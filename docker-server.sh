#!/bin/bash
# xSmartDeepResearch Docker Service Manager
# Manage local Docker container for testing

set -e

COMPOSE_FILE="deploy/docker-compose.local.yml"
CONTAINER_NAME="xsmart-local"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

case "$1" in
    start)
        print_status "Starting xSmartDeepResearch Docker container..."
        docker-compose -f $COMPOSE_FILE up -d
        print_success "Container started!"
        echo ""
        echo -e "Frontend: ${YELLOW}http://localhost:3080${NC}"
        echo -e "Backend:  ${YELLOW}http://localhost:3800${NC}"
        echo -e "Health:   ${YELLOW}http://localhost:3800/health${NC}"
        ;;
    
    stop)
        print_status "Stopping xSmartDeepResearch Docker container..."
        docker-compose -f $COMPOSE_FILE down
        print_success "Container stopped!"
        ;;
    
    restart)
        print_status "Restarting xSmartDeepResearch Docker container..."
        docker-compose -f $COMPOSE_FILE down
        docker-compose -f $COMPOSE_FILE up -d
        print_success "Container restarted!"
        ;;
    
    status)
        print_status "Container status:"
        docker ps -a --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        ;;
    
    logs)
        print_status "Showing container logs (Ctrl+C to exit)..."
        docker logs -f $CONTAINER_NAME
        ;;
    
    shell)
        print_status "Opening shell in container..."
        docker exec -it $CONTAINER_NAME /bin/bash
        ;;
    
    health)
        print_status "Checking health..."
        curl -s http://localhost:3800/health | python3 -m json.tool
        ;;
    
    build)
        print_status "Building Docker image..."
        docker build -t xsmart-deepresearch:1.0.0 -f deploy/Dockerfile.unified .
        print_success "Image built!"
        ;;
    
    *)
        echo "xSmartDeepResearch Docker Manager"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|shell|health|build}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the Docker container"
        echo "  stop    - Stop the Docker container"
        echo "  restart - Restart the Docker container"
        echo "  status  - Show container status"
        echo "  logs    - Show container logs (follow mode)"
        echo "  shell   - Open bash shell in container"
        echo "  health  - Check backend health endpoint"
        echo "  build   - Rebuild the Docker image"
        exit 1
        ;;
esac
