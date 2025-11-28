#!/bin/bash
# Script to manage the monitoring stack for ProjectHadesTesting

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

function print_help {
    echo -e "${YELLOW}HADES Monitoring Management${NC}"
    echo ""
    echo "Usage: ./monitoring.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start          Start the monitoring stack"
    echo "  stop           Stop the monitoring stack"
    echo "  restart        Restart the monitoring stack"
    echo "  status         Check status of monitoring services"
    echo "  logs           View logs from all monitoring services"
    echo "  help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./monitoring.sh start"
    echo "  ./monitoring.sh logs"
}

# Create the network if it doesn't exist
function create_network {
    if ! docker network inspect hades-monitoring &>/dev/null; then
        echo -e "${GREEN}Creating hades-monitoring network...${NC}"
        docker network create hades-monitoring
    fi
}

# Check if we're in the monitoring directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: Not in the monitoring directory.${NC}"
    echo "Please run this script from the monitoring directory."
    exit 1
fi

case "$1" in
    start)
        create_network
        echo -e "${GREEN}Starting monitoring stack...${NC}"
        docker-compose up -d
        
        echo -e "${GREEN}Monitoring stack is now running:${NC}"
        echo "- Grafana: http://localhost:3000 (admin/admin_password)"
        echo "- Prometheus: http://localhost:9090"
        echo "- Arize Phoenix: http://localhost:8084"
        echo "- cAdvisor: http://localhost:8082"
        ;;
    stop)
        echo -e "${YELLOW}Stopping monitoring stack...${NC}"
        docker-compose down
        ;;
    restart)
        echo -e "${YELLOW}Restarting monitoring stack...${NC}"
        docker-compose restart
        ;;
    status)
        echo -e "${GREEN}Monitoring stack status:${NC}"
        docker-compose ps
        ;;
    logs)
        echo -e "${GREEN}Viewing logs (Ctrl+C to exit)...${NC}"
        docker-compose logs -f
        ;;
    help|*)
        print_help
        ;;
esac
