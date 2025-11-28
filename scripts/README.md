# HADES Monitoring Scripts

This directory contains scripts for GPU and system monitoring within the HADES project. These scripts enable robust performance tracking of GPU usage during LLM experiments.

> **Note:** This directory is for core operational scripts only. For one-time repair scripts, temporary utilities, or other maintenance scripts, please use the `dev-utilities/` directory to keep the codebase clean and organized.

## Scripts Overview

### Main Launcher

- **start_monitoring.sh** - The main entry point script that orchestrates the entire monitoring infrastructure.
  - **Usage**: `./start_monitoring.sh`
  - **Purpose**: Starts the GPU metrics exporter, ensures Grafana dashboard persistence, and handles clean shutdown with dashboard backups.

### Core Metrics Collection

- **gpu_metrics_exporter.py** - Collects detailed metrics from NVIDIA RTX A6000 GPUs.
  - **Usage**: `python gpu_metrics_exporter.py`
  - **Purpose**: Continuously exports GPU metrics (utilization, memory, temperature, power) to Prometheus via node_exporter's textfile collector.

- **metrics_exporter.py** - Exports general system metrics to Prometheus.
  - **Usage**: `python metrics_exporter.py`
  - **Purpose**: Collects system-level metrics for overall performance monitoring.

### Grafana Dashboard Management

- **backup_grafana_dashboards.py** - Backs up Grafana dashboards to JSON files.
  - **Usage**: `python backup_grafana_dashboards.py`
  - **Purpose**: Ensures Grafana dashboards are version-controlled and persistent across restarts.

- **ensure_grafana_persistence.py** - Sets up default dashboards if none exist.
  - **Usage**: `python ensure_grafana_persistence.py`
  - **Purpose**: First-time setup and recovery tool to establish baseline monitoring dashboards.

### Troubleshooting

- **fix_gpu_metrics.py** - Diagnostic tool for fixing GPU metrics collection issues.
  - **Usage**: `python fix_gpu_metrics.py`
  - **Purpose**: Resolves common problems with GPU metrics collection, including permission issues and exporter failures.

## Monitoring Architecture

The HADES monitoring system uses:
- Node exporter's textfile collector for custom metrics
- Prometheus for time-series storage
- Grafana for visualization
- Docker for containerization

The monitoring dashboards are automatically provisioned from the `/ladon/grafana/provisioning/dashboards/json` directory.

## Common Tasks

1. **Start the entire monitoring stack**:
   ```
   cd /home/todd/ML-Lab/New-HADES/ladon
   docker-compose up -d
   ./scripts/start_monitoring.sh
   ```

2. **Manually backup Grafana dashboards**:
   ```
   python /home/todd/ML-Lab/New-HADES/ladon/scripts/backup_grafana_dashboards.py
   ```

3. **Troubleshoot GPU metrics**:
   ```
   python /home/todd/ML-Lab/New-HADES/ladon/scripts/fix_gpu_metrics.py
   ```

For more detailed information on GPU monitoring integration with LLM experiments, see `/docs/gpu_monitoring_for_llm.md`.

## Script Organization Guidelines

- **`/ladon/scripts/`** (this directory): Only for core operational scripts that are essential to the monitoring infrastructure and used regularly.
  
- **`/dev-utilities/`**: For one-time repair scripts, temporary utilities, debugging tools, or any scripts that aren't part of the regular operational flow. Using this directory for temporary scripts will prevent future cleanup efforts.
