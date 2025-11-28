# PathRAG Monitor

A visualization and monitoring tool for PathRAG graph traversal paths and performance metrics.

## Overview

This tool provides interactive visualizations of:
- PathRAG knowledge graph structure
- Query traversal paths
- Performance metrics and statistics
- Path selection analysis

## Setup

### Installation

```bash
cd /home/todd/ML-Lab/New-HADES/dev-utilities/pathrag-monitor
pip install -r requirements.txt
```

### Generate Sample Data (Development Only)

For development and testing, you can generate sample metrics data:

```bash
python metrics_collector.py --generate-samples --num-samples 100
```

### Launch the Dashboard

```bash
streamlit run app.py
```

## Usage

1. **Path Visualization**: Explore specific query paths through the knowledge graph
2. **Metrics Dashboard**: View performance trends and statistics
3. **Query Analysis**: Analyze query behavior and efficiency

## Integration with PathRAG

To add path tracking to PathRAG, the system needs to log traversal data during query processing. This can be implemented by:

1. Adding a path logger to PathRAG's retrieval system
2. Capturing metrics about traversal decisions and pruning
3. Storing metrics in SQLite or JSON format

## Future Enhancements

Once the monitoring tool is working properly, it will be moved to a containerized deployment in the `ladon/monitoring` stack.

## Directory Structure

```
pathrag-monitor/
├── app.py               # Streamlit application
├── metrics_collector.py # Data loading and processing
├── graph_visualizer.py  # NetworkX graph visualization
└── requirements.txt     # Dependencies
```
