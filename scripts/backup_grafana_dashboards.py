#!/usr/bin/env python3
"""
Enhanced Python script to backup Grafana dashboards with error handling.
This script ensures your dashboards persist across reboots by exporting them to JSON files.
"""

import os
import sys
import json
import time
import logging
import datetime
import requests
from pathlib import Path

# Configuration
GRAFANA_URL = "http://localhost:3000"
API_USER = "admin"
API_PASSWORD = "admin_password"  # Admin credentials from docker-compose
OUTPUT_DIR = "/home/todd/ML-Lab/New-HADES/ladon/grafana/provisioning/dashboards/json"
LOG_FILE = "/home/todd/ML-Lab/New-HADES/ladon/logs/grafana_backup.log"

# Create directories if they don't exist
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
Path("/home/todd/ML-Lab/New-HADES/ladon/logs").mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ],
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def wait_for_grafana():
    """Wait for Grafana to be fully up and running with retry logic."""
    logger.info("Starting Grafana dashboard backup...")
    
    for i in range(1, 31):
        try:
            response = requests.get(
                f"{GRAFANA_URL}/api/health",
                auth=(API_USER, API_PASSWORD),
                timeout=5
            )
            if response.status_code == 200:
                logger.info("Grafana is up and running!")
                return True
        except requests.RequestException:
            pass
        
        logger.info(f"Waiting for Grafana to start... (attempt {i}/30)")
        time.sleep(2)
    
    logger.error("ERROR: Grafana did not start in time")
    return False

def get_dashboard_list():
    """Get list of dashboards from Grafana."""
    try:
        response = requests.get(
            f"{GRAFANA_URL}/api/search?type=dash-db",
            auth=(API_USER, API_PASSWORD),
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"ERROR: Failed to get dashboard list: {e}")
        return []

def export_dashboard(uid):
    """Export a dashboard by UID and save to JSON file."""
    logger.info(f"Exporting dashboard with UID: {uid}")
    
    try:
        # Get dashboard JSON
        response = requests.get(
            f"{GRAFANA_URL}/api/dashboards/uid/{uid}",
            auth=(API_USER, API_PASSWORD),
            timeout=10
        )
        response.raise_for_status()
        dashboard_response = response.json()
        
        # Extract dashboard data
        dashboard_json = dashboard_response.get("dashboard", {})
        dashboard_title = dashboard_json.get("title", "unknown").replace(" ", "-").lower()
        
        # Create complete provisioning JSON with dashboard data
        output = {
            "annotations": {
                "list": dashboard_json.get("annotations", {}).get("list", [])
            },
            "editable": True,
            "fiscalYearStartMonth": 0,
            "graphTooltip": 0,
            "id": None,
            "links": [],
            "liveNow": False,
            "panels": dashboard_json.get("panels", []),
            "refresh": dashboard_json.get("refresh", "5s"),
            "schemaVersion": dashboard_json.get("schemaVersion", 38),
            "tags": dashboard_json.get("tags", []),
            "templating": dashboard_json.get("templating", {"list": []}),
            "time": dashboard_json.get("time", {"from": "now-6h", "to": "now"}),
            "timepicker": dashboard_json.get("timepicker", {}),
            "timezone": "browser",
            "title": dashboard_json.get("title"),
            "uid": dashboard_json.get("uid"),
            "version": dashboard_json.get("version", 1),
            "weekStart": ""
        }
        
        # Write to file
        output_path = os.path.join(OUTPUT_DIR, f"{dashboard_title}.json")
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"✅ Saved dashboard to {output_path}")
        return True
    except (requests.RequestException, json.JSONDecodeError, OSError) as e:
        logger.error(f"ERROR: Failed to export dashboard {uid}: {e}")
        return False

def create_example_dashboard():
    """Create an example GPU monitoring dashboard if none exist."""
    logger.info("Creating example GPU monitoring dashboard")
    try:
        example_path = "/home/todd/ML-Lab/New-HADES/ladon/grafana/examples/gpu-monitoring-dashboard.json"
        if os.path.exists(example_path):
            dest_path = os.path.join(OUTPUT_DIR, "gpu-monitoring-dashboard.json")
            with open(example_path, 'r') as src:
                with open(dest_path, 'w') as dst:
                    dst.write(src.read())
            logger.info(f"✅ Created example dashboard at {dest_path}")
    except OSError as e:
        logger.error(f"ERROR: Failed to create example dashboard: {e}")

def main():
    """Main function to backup all Grafana dashboards."""
    # Wait for Grafana to be available
    if not wait_for_grafana():
        sys.exit(1)
    
    # Get list of dashboards
    dashboard_list = get_dashboard_list()
    
    if not dashboard_list:
        logger.info("No dashboards found to export")
        create_example_dashboard()
        logger.info("Grafana dashboard backup complete! Your dashboards will persist across restarts.")
        return
    
    # Export each dashboard
    successful_exports = 0
    for dashboard in dashboard_list:
        uid = dashboard.get("uid")
        if uid and export_dashboard(uid):
            successful_exports += 1
    
    logger.info(f"Successfully exported {successful_exports} dashboards out of {len(dashboard_list)}")
    logger.info("Grafana dashboard backup complete! Your dashboards will persist across restarts.")

if __name__ == "__main__":
    main()
