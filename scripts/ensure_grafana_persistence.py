#!/usr/bin/env python3
"""
Script to handle Grafana persistence.
This script should be run at system startup to ensure dashboards are properly managed.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Configuration
LOG_FILE = "/home/todd/ML-Lab/New-HADES/ladon/logs/grafana_persistence.log"
GPU_EXAMPLE = "/home/todd/ML-Lab/New-HADES/ladon/grafana/examples/gpu-monitoring-dashboard.json"
DASHBOARD_DIR = "/home/todd/ML-Lab/New-HADES/ladon/grafana/provisioning/dashboards/json"

# Create log directory
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

def create_example_dashboard():
    """Create an example GPU monitoring dashboard."""
    gpu_example_dir = os.path.dirname(GPU_EXAMPLE)
    Path(gpu_example_dir).mkdir(parents=True, exist_ok=True)
    
    dashboard = {
        "annotations": {
            "list": []
        },
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 0,
        "id": None,
        "links": [],
        "liveNow": False,
        "panels": [
            {
                "datasource": {
                    "type": "prometheus",
                    "uid": "prometheus"
                },
                "fieldConfig": {
                    "defaults": {
                        "color": {
                            "mode": "thresholds"
                        },
                        "mappings": [],
                        "max": 100,
                        "min": 0,
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {
                                    "color": "green",
                                    "value": None
                                },
                                {
                                    "color": "orange",
                                    "value": 70
                                },
                                {
                                    "color": "red",
                                    "value": 85
                                }
                            ]
                        },
                        "unit": "percent"
                    },
                    "overrides": []
                },
                "gridPos": {
                    "h": 8,
                    "w": 12,
                    "x": 0,
                    "y": 0
                },
                "id": 1,
                "options": {
                    "orientation": "auto",
                    "reduceOptions": {
                        "calcs": [
                            "lastNotNull"
                        ],
                        "fields": "",
                        "values": False
                    },
                    "showThresholdLabels": False,
                    "showThresholdMarkers": True
                },
                "pluginVersion": "10.2.0",
                "targets": [
                    {
                        "datasource": {
                            "type": "prometheus",
                            "uid": "prometheus"
                        },
                        "editorMode": "code",
                        "expr": "nvidia_gpu_utilization{gpu=\"0\"}",
                        "instant": False,
                        "legendFormat": "GPU 0",
                        "range": True,
                        "refId": "A"
                    },
                    {
                        "datasource": {
                            "type": "prometheus",
                            "uid": "prometheus"
                        },
                        "editorMode": "code",
                        "expr": "nvidia_gpu_utilization{gpu=\"1\"}",
                        "hide": False,
                        "instant": False,
                        "legendFormat": "GPU 1",
                        "range": True,
                        "refId": "B"
                    }
                ],
                "title": "GPU Utilization",
                "type": "gauge"
            },
            {
                "datasource": {
                    "type": "prometheus",
                    "uid": "prometheus"
                },
                "fieldConfig": {
                    "defaults": {
                        "color": {
                            "mode": "palette-classic"
                        },
                        "custom": {
                            "axisCenteredZero": False,
                            "axisColorMode": "text",
                            "axisLabel": "",
                            "axisPlacement": "auto",
                            "barAlignment": 0,
                            "drawStyle": "line",
                            "fillOpacity": 10,
                            "gradientMode": "none",
                            "hideFrom": {
                                "legend": False,
                                "tooltip": False,
                                "viz": False
                            },
                            "insertNulls": False,
                            "lineInterpolation": "linear",
                            "lineWidth": 1,
                            "pointSize": 5,
                            "scaleDistribution": {
                                "type": "linear"
                            },
                            "showPoints": "never",
                            "spanNulls": False,
                            "stacking": {
                                "group": "A",
                                "mode": "none"
                            },
                            "thresholdsStyle": {
                                "mode": "off"
                            }
                        },
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {
                                    "color": "green",
                                    "value": None
                                },
                                {
                                    "color": "red",
                                    "value": 80
                                }
                            ]
                        },
                        "unit": "percent"
                    },
                    "overrides": []
                },
                "gridPos": {
                    "h": 8,
                    "w": 12,
                    "x": 12,
                    "y": 0
                },
                "id": 2,
                "options": {
                    "legend": {
                        "calcs": [
                            "mean",
                            "max"
                        ],
                        "displayMode": "table",
                        "placement": "right",
                        "showLegend": True
                    },
                    "tooltip": {
                        "mode": "single",
                        "sort": "none"
                    }
                },
                "targets": [
                    {
                        "datasource": {
                            "type": "prometheus",
                            "uid": "prometheus"
                        },
                        "editorMode": "code",
                        "expr": "nvidia_gpu_utilization{gpu=~\".*\"}",
                        "instant": False,
                        "legendFormat": "GPU {{gpu}}",
                        "range": True,
                        "refId": "A"
                    }
                ],
                "title": "GPU Utilization History",
                "type": "timeseries"
            }
        ],
        "refresh": "5s",
        "schemaVersion": 38,
        "tags": ["gpu", "monitoring", "nvidia"],
        "templating": {
            "list": []
        },
        "time": {
            "from": "now-15m",
            "to": "now"
        },
        "timepicker": {},
        "timezone": "browser",
        "title": "GPU Monitoring Dashboard",
        "uid": "gpu-monitoring",
        "version": 1,
        "weekStart": ""
    }
    
    # Write the dashboard JSON to file
    with open(GPU_EXAMPLE, 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    logger.info(f"Created example GPU dashboard at {GPU_EXAMPLE}")

def main():
    """Main function to ensure Grafana persistence."""
    logger.info("Starting Grafana persistence check...")
    
    # Create dashboard directory if it doesn't exist
    Path(DASHBOARD_DIR).mkdir(parents=True, exist_ok=True)
    
    # Check if the dashboard directory is empty
    if any(Path(DASHBOARD_DIR).iterdir()):
        logger.info("Dashboard directory already has content, no need for default dashboards")
    else:
        logger.info("No dashboards found, creating GPU monitoring example dashboard")
        
        # Create the example dashboard if it doesn't exist
        if not os.path.exists(GPU_EXAMPLE):
            create_example_dashboard()
        
        # Copy the example to the provisioning directory
        dashboard_name = os.path.basename(GPU_EXAMPLE)
        target_path = os.path.join(DASHBOARD_DIR, dashboard_name)
        
        with open(GPU_EXAMPLE, 'r') as src:
            with open(target_path, 'w') as dst:
                dst.write(src.read())
        
        logger.info(f"GPU dashboard example copied to {target_path}")
    
    logger.info("Grafana persistence check complete!")

if __name__ == "__main__":
    main()
