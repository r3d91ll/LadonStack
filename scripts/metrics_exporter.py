#!/usr/bin/env python3
"""
Metrics exporter for HADES experiments.
Collects system metrics and custom experiment metrics and exposes them 
via a Prometheus endpoint.
"""

import os
import time
import threading
import psutil
from prometheus_client import start_http_server, Gauge, Counter, Summary, Histogram
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('metrics_exporter')

# Get configuration from environment variables
METRICS_PORT = int(os.environ.get('METRICS_PORT', 9000))
COLLECTION_INTERVAL = int(os.environ.get('METRICS_INTERVAL', 15))  # seconds

# Define metrics
# System metrics
CPU_USAGE = Gauge('hades_cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('hades_memory_usage_bytes', 'Memory usage in bytes')
MEMORY_PERCENT = Gauge('hades_memory_usage_percent', 'Memory usage percentage')
DISK_USAGE = Gauge('hades_disk_usage_bytes', 'Disk usage in bytes')
DISK_PERCENT = Gauge('hades_disk_usage_percent', 'Disk usage percentage')

# Experiment metrics
EXPERIMENT_RUNNING = Gauge('hades_experiment_running', 'Experiment running status', ['experiment', 'phase'])
QUERY_COUNT = Counter('hades_query_count_total', 'Total number of queries processed', ['experiment', 'phase'])
QUERY_LATENCY = Histogram('hades_query_latency_seconds', 'Query latency in seconds', ['experiment', 'phase'])
PATH_LENGTH = Histogram('hades_path_length', 'Number of nodes in retrieved paths', ['experiment', 'phase']) 
RETRIEVAL_PRECISION = Gauge('hades_retrieval_precision', 'Precision of retrieval', ['experiment', 'phase'])
RETRIEVAL_RECALL = Gauge('hades_retrieval_recall', 'Recall of retrieval', ['experiment', 'phase'])
MODEL_TOKENS = Counter('hades_model_tokens_total', 'Total number of tokens used by the model', ['model', 'type'])

# Neo4j specific metrics (for GraphRAG)
NEO4J_QUERY_COUNT = Counter('hades_neo4j_query_count_total', 'Total number of Neo4j queries', ['type'])
NEO4J_QUERY_TIME = Histogram('hades_neo4j_query_time_seconds', 'Neo4j query time in seconds', ['type'])

# PathRAG specific metrics (NetworkX)
PATHRAG_GRAPH_NODES = Gauge('hades_pathrag_graph_nodes', 'Number of nodes in PathRAG graph')
PATHRAG_GRAPH_EDGES = Gauge('hades_pathrag_graph_edges', 'Number of edges in PathRAG graph')
PATHRAG_TRAVERSAL_TIME = Histogram('hades_pathrag_traversal_time_seconds', 'PathRAG graph traversal time')


def collect_system_metrics():
    """Collect system metrics and update Prometheus gauges."""
    while True:
        try:
            # CPU metrics
            CPU_USAGE.set(psutil.cpu_percent(interval=1))
            
            # Memory metrics
            memory = psutil.virtual_memory()
            MEMORY_USAGE.set(memory.used)
            MEMORY_PERCENT.set(memory.percent)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            DISK_USAGE.set(disk.used)
            DISK_PERCENT.set(disk.percent)
            
            time.sleep(COLLECTION_INTERVAL)
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            time.sleep(5)  # Wait before retrying

def start_metrics_server():
    """Start the Prometheus metrics server."""
    try:
        start_http_server(METRICS_PORT)
        logger.info(f"Started metrics server on port {METRICS_PORT}")
        
        # Start collecting system metrics in a background thread
        metrics_thread = threading.Thread(target=collect_system_metrics, daemon=True)
        metrics_thread.start()
        
        logger.info("Metrics collection started")
    except Exception as e:
        logger.error(f"Error starting metrics server: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting HADES metrics exporter")
    start_metrics_server()
    
    # Keep the main thread alive
    while True:
        time.sleep(60)
