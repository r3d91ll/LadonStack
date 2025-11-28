#!/usr/bin/env python3
"""
Simple GPU metrics exporter for Prometheus.

This script runs nvidia-smi and exposes basic GPU metrics in Prometheus format.
Much simpler than DCGM and doesn't require NVIDIA Container Toolkit.
"""

import subprocess
import time
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
import json


class GPUMetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            try:
                metrics = get_gpu_metrics()
                self.send_response(200)
                self.send_header('Content-type', 'text/plain; version=0.0.4; charset=utf-8')
                self.end_headers()
                self.wfile.write(metrics.encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(f"Error: {str(e)}".encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default logging to reduce noise
        pass


def get_gpu_metrics():
    """Get GPU metrics from nvidia-smi and format for Prometheus."""
    try:
        # Run nvidia-smi with JSON output
        cmd = [
            'nvidia-smi', 
            '--query-gpu=index,name,temperature.gpu,utilization.gpu,utilization.memory,memory.total,memory.used,memory.free,power.draw,power.limit',
            '--format=csv,noheader,nounits'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            raise Exception(f"nvidia-smi failed: {result.stderr}")
        
        lines = result.stdout.strip().split('\n')
        metrics = []
        
        # Add metric headers
        metrics.append("# HELP nvidia_gpu_temperature_celsius GPU temperature in Celsius")
        metrics.append("# TYPE nvidia_gpu_temperature_celsius gauge")
        
        metrics.append("# HELP nvidia_gpu_utilization_percent GPU utilization percentage")
        metrics.append("# TYPE nvidia_gpu_utilization_percent gauge")
        
        metrics.append("# HELP nvidia_gpu_memory_utilization_percent GPU memory utilization percentage")
        metrics.append("# TYPE nvidia_gpu_memory_utilization_percent gauge")
        
        metrics.append("# HELP nvidia_gpu_memory_total_bytes GPU total memory in bytes")
        metrics.append("# TYPE nvidia_gpu_memory_total_bytes gauge")
        
        metrics.append("# HELP nvidia_gpu_memory_used_bytes GPU used memory in bytes")
        metrics.append("# TYPE nvidia_gpu_memory_used_bytes gauge")
        
        metrics.append("# HELP nvidia_gpu_memory_free_bytes GPU free memory in bytes")
        metrics.append("# TYPE nvidia_gpu_memory_free_bytes gauge")
        
        metrics.append("# HELP nvidia_gpu_power_draw_watts GPU power draw in watts")
        metrics.append("# TYPE nvidia_gpu_power_draw_watts gauge")
        
        metrics.append("# HELP nvidia_gpu_power_limit_watts GPU power limit in watts")
        metrics.append("# TYPE nvidia_gpu_power_limit_watts gauge")
        
        # Process each GPU
        for line in lines:
            if not line.strip():
                continue
                
            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 10:
                continue
                
            try:
                gpu_index = parts[0]
                gpu_name = parts[1].replace(' ', '_')
                temp = float(parts[2]) if parts[2] != '[Not Supported]' else 0
                util_gpu = float(parts[3]) if parts[3] != '[Not Supported]' else 0
                util_mem = float(parts[4]) if parts[4] != '[Not Supported]' else 0
                mem_total = float(parts[5]) * 1024 * 1024 if parts[5] != '[Not Supported]' else 0  # MB to bytes
                mem_used = float(parts[6]) * 1024 * 1024 if parts[6] != '[Not Supported]' else 0   # MB to bytes
                mem_free = float(parts[7]) * 1024 * 1024 if parts[7] != '[Not Supported]' else 0   # MB to bytes
                power_draw = float(parts[8]) if parts[8] != '[Not Supported]' else 0
                power_limit = float(parts[9]) if parts[9] != '[Not Supported]' else 0
                
                # Add metrics for this GPU
                labels = f'gpu="{gpu_index}",name="{gpu_name}"'
                
                metrics.append(f'nvidia_gpu_temperature_celsius{{{labels}}} {temp}')
                metrics.append(f'nvidia_gpu_utilization_percent{{{labels}}} {util_gpu}')
                metrics.append(f'nvidia_gpu_memory_utilization_percent{{{labels}}} {util_mem}')
                metrics.append(f'nvidia_gpu_memory_total_bytes{{{labels}}} {int(mem_total)}')
                metrics.append(f'nvidia_gpu_memory_used_bytes{{{labels}}} {int(mem_used)}')
                metrics.append(f'nvidia_gpu_memory_free_bytes{{{labels}}} {int(mem_free)}')
                metrics.append(f'nvidia_gpu_power_draw_watts{{{labels}}} {power_draw}')
                metrics.append(f'nvidia_gpu_power_limit_watts{{{labels}}} {power_limit}')
                
            except (ValueError, IndexError) as e:
                print(f"Error parsing GPU data: {e}")
                continue
        
        # Add a simple up metric
        metrics.append("# HELP nvidia_gpu_exporter_up Whether the exporter is working")
        metrics.append("# TYPE nvidia_gpu_exporter_up gauge")
        metrics.append("nvidia_gpu_exporter_up 1")
        
        return '\n'.join(metrics) + '\n'
        
    except subprocess.TimeoutExpired:
        raise Exception("nvidia-smi timeout")
    except FileNotFoundError:
        raise Exception("nvidia-smi not found")
    except Exception as e:
        raise Exception(f"Failed to get GPU metrics: {str(e)}")


def main():
    """Run the GPU metrics HTTP server."""
    server_address = ('', 9445)
    httpd = HTTPServer(server_address, GPUMetricsHandler)
    
    print("Starting GPU metrics exporter on port 9445...")
    print("Metrics available at http://localhost:9445/metrics")
    
    try:
        # Test nvidia-smi first
        test_metrics = get_gpu_metrics()
        print("✓ nvidia-smi working, found metrics")
        
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        httpd.shutdown()
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == '__main__':
    main()