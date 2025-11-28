#!/bin/bash
# Main monitoring script for HADES - the only shell script we keep
# All other functionality has been migrated to Python scripts

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create a unique session ID for this run
SESSION_ID=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/home/todd/ML-Lab/New-HADES/ladon/logs/monitoring_${SESSION_ID}.log"
mkdir -p /home/todd/ML-Lab/New-HADES/ladon/logs

# Log function that shows output and writes to file
log() {
    echo -e "${1}" | tee -a "$LOG_FILE"
}

log "${BLUE}=============================================${NC}"
log "${BLUE}  HADES Monitoring System Starting - ${SESSION_ID}  ${NC}"
log "${BLUE}=============================================${NC}"

# Run the Grafana persistence setup
if [ -f "/home/todd/ML-Lab/New-HADES/ladon/scripts/ensure_grafana_persistence.py" ]; then
    log "${GREEN}Setting up Grafana dashboard persistence...${NC}"
    python /home/todd/ML-Lab/New-HADES/ladon/scripts/ensure_grafana_persistence.py
    log "${GREEN}Grafana persistence setup complete${NC}"
else
    log "${YELLOW}Grafana persistence script not found${NC}"
fi

# Export GPU metrics
if [ -f "/home/todd/ML-Lab/New-HADES/ladon/scripts/gpu_metrics_exporter.py" ]; then
    log "${GREEN}Starting GPU metrics exporter...${NC}"
    python /home/todd/ML-Lab/New-HADES/ladon/scripts/gpu_metrics_exporter.py &
    GPU_METRICS_PID=$!
    log "${GREEN}GPU metrics exporter started with PID ${GPU_METRICS_PID}${NC}"
else
    log "${YELLOW}GPU metrics exporter not found${NC}"
fi

# Create a trap to backup Grafana dashboards on exit
backup_on_exit() {
    log "${YELLOW}Detected shutdown, backing up Grafana dashboards...${NC}"
    # Only run if the backup script exists
    if [ -f "/home/todd/ML-Lab/New-HADES/ladon/scripts/backup_grafana_dashboards.py" ]; then
        python /home/todd/ML-Lab/New-HADES/ladon/scripts/backup_grafana_dashboards.py
        log "${GREEN}Grafana dashboards backed up successfully${NC}"
    else
        log "${RED}Backup script not found${NC}"
    fi
    
    # If we were running the metrics exporter, stop it
    if [ ! -z "$METRICS_PID" ]; then
        log "${YELLOW}Stopping metrics exporter...${NC}"
        kill $METRICS_PID 2>/dev/null || true
    fi
    
    # If we were running the GPU metrics exporter, stop it
    if [ ! -z "$GPU_METRICS_PID" ]; then
        log "${YELLOW}Stopping GPU metrics exporter...${NC}"
        kill $GPU_METRICS_PID 2>/dev/null || true
    fi
    
    log "${BLUE}=============================================${NC}"
    log "${BLUE}  HADES Monitoring System Shutdown - ${SESSION_ID}  ${NC}"
    log "${BLUE}=============================================${NC}"
    exit
}

# Register the trap for clean shutdown
trap backup_on_exit SIGTERM SIGINT SIGHUP

# Check if metrics are enabled
if [ "${ENABLE_METRICS}" = "true" ]; then
    log "${GREEN}Starting metrics exporter on port ${METRICS_PORT}...${NC}"
    
    # Start the metrics exporter in the background
    python /home/todd/ML-Lab/New-HADES/ladon/scripts/metrics_exporter.py &
    METRICS_PID=$!
    
    log "${GREEN}Metrics exporter started with PID ${METRICS_PID}${NC}"
else
    log "${YELLOW}Metrics collection is disabled${NC}"
fi

# If a command was passed to the container, execute it
if [ $# -gt 0 ]; then
    log "${GREEN}Executing command: $@${NC}"
    exec "$@"
else
    # Otherwise, just keep the container running
    log "${GREEN}No command specified, container will remain running${NC}"
    log "${GREEN}Your Grafana dashboards will be automatically backed up on shutdown${NC}"
    log "${GREEN}Press Ctrl+C to exit${NC}"
    
    # Keep this script running until terminated
    tail -f /dev/null
fi
