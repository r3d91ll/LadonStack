#!/usr/bin/env python3
"""
GPU Metrics Exporter - Custom Prometheus exporter for NVIDIA GPU metrics
This script collects GPU metrics using nvidia-smi and exposes them via a Prometheus endpoint.
Useful for monitoring GPU utilization, memory usage, and temperature in the PathRAG and GraphRAG experiments.
"""

import subprocess
import time
import logging
from prometheus_client import start_http_server, Gauge

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('gpu-metrics-exporter')

# Define Prometheus metrics
GPU_UTILIZATION = Gauge('gpu_utilization_percent', 'GPU utilization percentage', ['gpu_id', 'gpu_name'])
GPU_MEMORY_USED = Gauge('gpu_memory_used_mb', 'GPU memory used in MB', ['gpu_id', 'gpu_name'])
GPU_MEMORY_TOTAL = Gauge('gpu_memory_total_mb', 'GPU total memory in MB', ['gpu_id', 'gpu_name'])
GPU_TEMPERATURE = Gauge('gpu_temperature_celsius', 'GPU temperature in Celsius', ['gpu_id', 'gpu_name'])
GPU_POWER_USAGE = Gauge('gpu_power_usage_watts', 'GPU power usage in Watts', ['gpu_id', 'gpu_name'])
GPU_POWER_LIMIT = Gauge('gpu_power_limit_watts', 'GPU power limit in Watts', ['gpu_id', 'gpu_name'])

def parse_nvidia_smi():
    """Parse output from nvidia-smi command to extract GPU metrics."""
    try:
        # Run nvidia-smi with query format to get metrics
        # We'll first check if nvidia-smi is available
        try:
            subprocess.run(['which', 'nvidia-smi'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            logger.error("nvidia-smi not found in PATH. Using host path.")
            # Explicitly use the full path mapped from the host
            nvidia_smi_path = '/usr/bin/nvidia-smi'
        else:
            nvidia_smi_path = 'nvidia-smi'
            
        cmd = [
            nvidia_smi_path, 
            '--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw,power.limit',
            '--format=csv,noheader,nounits'
        ]
        process = subprocess.run(cmd, check=True, capture_output=True)
        result = process.stdout.decode('utf-8').strip()
        
        # Parse each line (one per GPU)
        for line in result.split('\n'):
            if not line:
                continue
                
            # Split by comma and strip whitespace
            values = [x.strip() for x in line.split(',')]
            
            if len(values) >= 8:
                gpu_id = values[0]
                gpu_name = values[1]
                gpu_util = float(values[2])
                mem_used = float(values[3])
                mem_total = float(values[4])
                temperature = float(values[5])
                
                # Power values might be N/A for some GPUs
                power_usage = 0.0
                power_limit = 0.0
                
                try:
                    power_usage = float(values[6])
                    power_limit = float(values[7])
                except ValueError:
                    logger.warning(f"Could not parse power values for GPU {gpu_id}")
                
                # Update Prometheus metrics
                GPU_UTILIZATION.labels(gpu_id=gpu_id, gpu_name=gpu_name).set(gpu_util)
                GPU_MEMORY_USED.labels(gpu_id=gpu_id, gpu_name=gpu_name).set(mem_used)
                GPU_MEMORY_TOTAL.labels(gpu_id=gpu_id, gpu_name=gpu_name).set(mem_total)
                GPU_TEMPERATURE.labels(gpu_id=gpu_id, gpu_name=gpu_name).set(temperature)
                GPU_POWER_USAGE.labels(gpu_id=gpu_id, gpu_name=gpu_name).set(power_usage)
                GPU_POWER_LIMIT.labels(gpu_id=gpu_id, gpu_name=gpu_name).set(power_limit)
                
                logger.info(f"GPU {gpu_id} ({gpu_name}): Utilization: {gpu_util}%, Memory: {mem_used}/{mem_total} MB, Temp: {temperature}°C")
            else:
                logger.warning(f"Unexpected format from nvidia-smi: {line}")
                
    except FileNotFoundError:
        logger.error("nvidia-smi command not found. Is NVIDIA driver installed?")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing nvidia-smi: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

def main():
    """Main function to start the exporter."""
    # Start up the server to expose the metrics
    port = 9400
    start_http_server(port)
    logger.info(f"GPU Metrics Exporter started on port {port}")
    
    # Check for metrics every 5 seconds
    while True:
        try:
            parse_nvidia_smi()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        
        time.sleep(5)

if __name__ == '__main__':
    main()
