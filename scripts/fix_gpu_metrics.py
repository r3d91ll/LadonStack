#!/usr/bin/env python3
"""
Script to fix GPU monitoring metrics collection for NVIDIA RTX A6000 GPUs.
This script ensures proper setup of the GPU metrics collection infrastructure.
"""

import os
import time
import subprocess
import requests
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def run_command(command, shell=True, check=True):
    """Run a shell command and return the output."""
    try:
        result = subprocess.run(
            command,
            shell=shell,
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        logger.error(f"Error output: {e.stderr}")
        return None

def stop_existing_exporters():
    """Stop any existing GPU metrics exporters."""
    logger.info("Stopping any existing GPU metrics exporters...")
    run_command("pkill -f gpu_metrics_exporter.sh 2>/dev/null || true", check=False)

def ensure_metrics_directory():
    """Ensure the metrics directory exists with proper permissions."""
    logger.info("Ensuring metrics directory exists with proper permissions...")
    
    # Using sudo requires password, so we'll try to create directories without sudo first
    try:
        os.makedirs("/tmp/node_exporter_metrics", exist_ok=True)
    except PermissionError:
        logger.info("Using sudo to create metrics directory...")
        run_command("sudo mkdir -p /tmp/node_exporter_metrics")
    
    # Set permissions
    try:
        os.chmod("/tmp/node_exporter_metrics", 0o777)
    except PermissionError:
        logger.info("Using sudo to set directory permissions...")
        run_command("sudo chmod 777 /tmp/node_exporter_metrics")
    
    # Create log file if it doesn't exist and set permissions
    try:
        with open("/tmp/gpu_exporter.log", "a"):
            pass
        os.chmod("/tmp/gpu_exporter.log", 0o777)
    except PermissionError:
        logger.info("Using sudo to set log file permissions...")
        run_command("sudo touch /tmp/gpu_exporter.log")
        run_command("sudo chmod 777 /tmp/gpu_exporter.log")

def create_test_metric():
    """Create a simple tester metrics file to verify collection is working."""
    logger.info("Creating test metric file...")
    test_metric_content = """# HELP test_metric A test metric to verify prometheus collection
# TYPE test_metric gauge
test_metric{source="host"} 1
"""
    with open("/tmp/node_exporter_metrics/test_metric.prom", "w") as f:
        f.write(test_metric_content)

def start_gpu_exporter():
    """Restart the GPU metrics exporter with correct permissions."""
    logger.info("Starting GPU metrics exporter...")
    exporter_script = "/home/todd/ML-Lab/New-HADES/ladon/scripts/gpu_metrics_exporter.sh"
    
    # Start the exporter as a background process
    run_command(f"nohup {exporter_script} > /tmp/gpu_exporter.log 2>&1 &")

def check_metrics_generation():
    """Check if metrics are being generated."""
    logger.info("Waiting for the first metrics collection cycle...")
    time.sleep(6)
    
    metrics_file = "/tmp/node_exporter_metrics/gpu_metrics.prom"
    if os.path.exists(metrics_file):
        logger.info("✅ GPU metrics successfully generated")
        logger.info("Sample metrics:")
        
        with open(metrics_file, "r") as f:
            sample = "\n".join(f.readlines()[:20])
            logger.info(sample)
        
        return True
    else:
        logger.error("❌ GPU metrics file not created")
        logger.error("Checking log file for errors:")
        
        try:
            with open("/tmp/gpu_exporter.log", "r") as f:
                log_tail = "\n".join(f.readlines()[-20:])
                logger.error(log_tail)
        except FileNotFoundError:
            logger.error("Log file not found")
        
        return False

def restart_node_exporter():
    """Restart the node-exporter container to ensure it picks up the new metrics."""
    logger.info("Restarting node-exporter container...")
    run_command("docker restart node-exporter")
    
    # Wait for node-exporter to start up
    logger.info("Waiting for node-exporter to start...")
    time.sleep(5)

def verify_metrics_collection():
    """Verify metrics collection via node-exporter."""
    logger.info("Checking metrics via node-exporter...")
    try:
        response = requests.get("http://localhost:9100/metrics", timeout=5)
        if response.status_code == 200:
            # Filter for GPU or test metrics
            metrics = response.text.split("\n")
            gpu_metrics = [line for line in metrics if any(x in line for x in ["gpu_", "test_metric"])][:10]
            
            if gpu_metrics:
                logger.info("Found GPU metrics via node-exporter:")
                for metric in gpu_metrics:
                    logger.info(f"  {metric}")
            else:
                logger.warning("No GPU metrics found in node-exporter output")
        else:
            logger.error(f"Failed to get metrics from node-exporter: HTTP {response.status_code}")
    except requests.RequestException as e:
        logger.error(f"Error connecting to node-exporter: {e}")

def main():
    """Main function to fix GPU metrics collection."""
    logger.info("Starting GPU metrics fix script...")
    
    # Step 1: Stop any existing exporters
    stop_existing_exporters()
    
    # Step 2: Ensure metrics directory exists
    ensure_metrics_directory()
    
    # Step 3: Create test metric
    create_test_metric()
    
    # Step 4: Start GPU exporter
    start_gpu_exporter()
    
    # Step 5: Check if metrics are being generated
    metrics_ok = check_metrics_generation()
    
    # Step 6: Restart node-exporter container
    restart_node_exporter()
    
    # Step 7: Verify metrics collection
    verify_metrics_collection()
    
    logger.info("")
    logger.info("Monitor Grafana at http://localhost:3000 to see if metrics appear.")
    logger.info("Check the GPU dashboard for your NVIDIA RTX A6000 GPUs.")
    
    return 0 if metrics_ok else 1

if __name__ == "__main__":
    sys.exit(main())
