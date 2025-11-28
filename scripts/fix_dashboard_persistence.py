#!/usr/bin/env python3
"""
Fix Grafana dashboard persistence issues by:
1. Cleaning up UID conflicts
2. Properly backing up custom dashboards
3. Ensuring provisioned dashboards don't conflict with UI changes
"""

import os
import sys
import json
import time
import logging
import requests
from pathlib import Path

# Configuration
GRAFANA_URL = "http://localhost:3000"
API_USER = "admin"
API_PASSWORD = "admin_password"
BASE_DIR = "/home/todd/ML-Lab/Olympus/ladon"
PROVISIONED_DIR = f"{BASE_DIR}/grafana/provisioning/dashboards/json"
CUSTOM_DIR = f"{BASE_DIR}/grafana/provisioning/dashboards/custom"
LOG_FILE = f"{BASE_DIR}/logs/dashboard_fix.log"

# Create directories
Path(CUSTOM_DIR).mkdir(parents=True, exist_ok=True)
Path(f"{BASE_DIR}/logs").mkdir(parents=True, exist_ok=True)

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
    """Wait for Grafana to be available."""
    logger.info("Waiting for Grafana to be available...")
    for i in range(30):
        try:
            response = requests.get(f"{GRAFANA_URL}/api/health", timeout=5)
            if response.status_code == 200:
                logger.info("Grafana is available!")
                return True
        except requests.RequestException:
            pass
        time.sleep(2)
    logger.error("Grafana not available after 60 seconds")
    return False

def get_provisioned_uids():
    """Get UIDs of all provisioned dashboards."""
    provisioned_uids = set()
    for json_file in Path(PROVISIONED_DIR).glob("*.json"):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                if 'uid' in data:
                    provisioned_uids.add(data['uid'])
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Could not read {json_file}: {e}")
    return provisioned_uids

def get_database_dashboards():
    """Get all dashboards from Grafana database."""
    try:
        response = requests.get(
            f"{GRAFANA_URL}/api/search?type=dash-db",
            auth=(API_USER, API_PASSWORD),
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Failed to get dashboards: {e}")
        return []

def delete_dashboard(uid):
    """Delete a dashboard by UID."""
    try:
        response = requests.delete(
            f"{GRAFANA_URL}/api/dashboards/uid/{uid}",
            auth=(API_USER, API_PASSWORD),
            timeout=10
        )
        if response.status_code == 200:
            logger.info(f"Deleted dashboard {uid}")
            return True
        else:
            logger.warning(f"Could not delete dashboard {uid}: {response.status_code}")
            return False
    except requests.RequestException as e:
        logger.error(f"Error deleting dashboard {uid}: {e}")
        return False

def backup_custom_dashboard(uid, title):
    """Backup a custom dashboard to the custom directory."""
    try:
        response = requests.get(
            f"{GRAFANA_URL}/api/dashboards/uid/{uid}",
            auth=(API_USER, API_PASSWORD),
            timeout=10
        )
        response.raise_for_status()
        dashboard_data = response.json()
        
        # Extract dashboard JSON
        dashboard = dashboard_data.get("dashboard", {})
        
        # Create a safe filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '-').lower()
        filename = f"{safe_title}.json"
        
        # Save to custom directory
        output_path = Path(CUSTOM_DIR) / filename
        with open(output_path, 'w') as f:
            json.dump(dashboard, f, indent=2)
        
        logger.info(f"Backed up custom dashboard '{title}' to {output_path}")
        return True
    except (requests.RequestException, json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to backup dashboard {uid}: {e}")
        return False

def main():
    """Main function to fix dashboard persistence."""
    logger.info("Starting dashboard persistence fix...")
    
    if not wait_for_grafana():
        sys.exit(1)
    
    # Get provisioned UIDs
    provisioned_uids = get_provisioned_uids()
    logger.info(f"Found {len(provisioned_uids)} provisioned dashboard UIDs")
    
    # Get database dashboards
    db_dashboards = get_database_dashboards()
    logger.info(f"Found {len(db_dashboards)} dashboards in database")
    
    # Process each dashboard
    for dashboard in db_dashboards:
        uid = dashboard.get('uid')
        title = dashboard.get('title', 'Unknown')
        
        if not uid:
            continue
            
        if uid in provisioned_uids:
            # This is a conflict - delete from database so provisioned version loads
            logger.info(f"Removing conflicting dashboard '{title}' (UID: {uid}) from database")
            delete_dashboard(uid)
        else:
            # This is a custom dashboard - back it up
            logger.info(f"Backing up custom dashboard '{title}' (UID: {uid})")
            backup_custom_dashboard(uid, title)
    
    logger.info("Dashboard persistence fix complete!")
    logger.info("Restart Grafana to see the changes take effect")

if __name__ == "__main__":
    main()