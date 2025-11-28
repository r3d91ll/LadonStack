# LadonStack

**GPU-Focused Monitoring and Observability Stack**

LadonStack the my prefered monitoring stack for GPU-accelerated ML/AI workloads. It provides real-time visibility into NVIDIA GPU metrics, system performance, and ML model observability.

Named after the hundred-headed dragon that guarded the golden apples of the Hesperides in Greek mythology, Ladon vigilantly monitors all aspects of your GPU computing environment.

## Features

- **NVIDIA DCGM Integration** - Full DCGM exporter for comprehensive GPU metrics
- **Prometheus + Grafana** - Industry-standard metrics collection and visualization
- **Arize Phoenix** - ML model observability and trace analysis
- **Pre-configured Dashboards** - Ready-to-use GPU and system dashboards
- **Alert Rules** - Built-in alerts for GPU temperature, memory, and system health
- **Portable** - Standalone stack that can run on any Linux machine with Docker

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Ladon Stack                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Grafana    │◄───│  Prometheus  │◄───│    DCGM      │  │
│  │   :3000      │    │    :9090     │    │   :9400      │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│         │                   ▲                   ▲           │
│         │                   │                   │           │
│         ▼                   │                   │           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Phoenix    │    │Node Exporter │    │   Process    │  │
│  │   :8084      │    │    :9100     │    │   Exporter   │  │
│  └──────────────┘    └──────────────┘    │    :9256     │  │
│                                          └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### A Note on Deployment Architecture

**This is a "I spent all my budget on a Threadripper and can't afford another server" deployment.**

In a production environment following best practices, you would typically:
- Run **DCGM exporter** on each GPU server (lightweight, just exposes metrics)
- Run **node_exporter** on each monitored host (standard Linux practice)
- Deploy **Prometheus and Grafana** on a dedicated monitoring/logging server
- Use proper service discovery or static configs to scrape remote targets

This all-in-one deployment runs everything on the same machine—the GPU workstation itself. While this works and is certainly better than no monitoring at all, it means your monitoring stack competes for resources with your actual workloads and creates a single point of failure.

**When hardware budgets allow**, consider separating concerns: exporters on compute nodes, aggregation and visualization on dedicated infrastructure. Until then, this stack provides solid observability for single-machine GPU workstations.

## Quick Start

### Prerequisites

- Docker and Docker Compose v2+
- NVIDIA GPU with drivers installed
- NVIDIA Container Toolkit (`nvidia-docker2`)
- Linux host (tested on Ubuntu 22.04+)

### Installation

```bash
# Clone the repository
git clone https://github.com/r3d91ll/LadonStack.git
cd LadonStack

# Start core services (without GPU monitoring)
docker compose up -d

# OR: Start with GPU monitoring (requires NVIDIA Container Toolkit)
docker compose --profile gpu up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f
```

### Service Endpoints

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://localhost:3000 | admin / admin |
| **Prometheus** | http://localhost:9090 | - |
| **Phoenix** | http://localhost:8084 | - |
| **Node Exporter** | http://localhost:9100/metrics | - |
| **DCGM Exporter** | http://localhost:9400/metrics | - |
| **Process Exporter** | http://localhost:9256/metrics | - |

## GPU Metrics (via DCGM)

The DCGM exporter provides comprehensive GPU metrics including:

- **Utilization**: GPU core, memory controller, encoder/decoder
- **Memory**: Total, used, free VRAM
- **Temperature**: GPU core temperature
- **Power**: Current draw, power limit, throttling reasons
- **Clocks**: SM, memory, graphics clock frequencies
- **Errors**: ECC errors, XID errors
- **PCIe**: Throughput, link state

### Example Prometheus Queries

```promql
# GPU temperature by device
DCGM_FI_DEV_GPU_TEMP

# GPU utilization percentage
DCGM_FI_DEV_GPU_UTIL

# Memory used (bytes)
DCGM_FI_DEV_FB_USED

# Power usage (watts)
DCGM_FI_DEV_POWER_USAGE
```

## Pre-configured Dashboards

1. **Node Exporter Full** - Comprehensive system metrics
   - CPU, memory, disk, network utilization
   - System load and process statistics
   - Filesystem usage and I/O metrics

2. **NVIDIA GPU Monitoring** - GPU-specific dashboard
   - GPU utilization and memory usage
   - Temperature and power consumption
   - SM clock speeds and throttling

3. **Real-Time GPU Metrics** - Live GPU performance
   - Multi-GPU support
   - Historical trends
   - Performance correlation analysis

## Alert Rules

Built-in alerts in `prometheus/alert_rules.yml`:

**GPU Alerts:**
- `GPUHighTemperature` - GPU > 80°C for 5 minutes
- `GPUCriticalTemperature` - GPU > 90°C for 1 minute
- `GPUHighMemoryUsage` - GPU memory > 90% for 5 minutes
- `GPUHighPowerUsage` - GPU power > 300W for 5 minutes

**System Alerts:**
- `HighCPUUsage` - CPU > 80% for 5 minutes
- `HighMemoryUsage` - Memory > 85% for 5 minutes
- `DiskSpaceWarning` - Disk > 80% full
- `DiskSpaceCritical` - Disk > 95% full
- `TargetDown` - Any Prometheus target down for 2 minutes

## Configuration

### Adding Custom Scrape Targets

Edit `prometheus/prometheus.yml`:

```yaml
scrape_configs:
  # Add your application
  - job_name: 'my-app'
    static_configs:
      - targets: ['172.28.0.1:8080']  # Docker gateway for host apps
        labels:
          service: 'my-app'
    metrics_path: '/metrics'
```

Then reload Prometheus:
```bash
docker compose restart prometheus
```

### Environment Variables

Create a `.env` file for custom configuration:

```bash
# Grafana
GF_SECURITY_ADMIN_PASSWORD=your_secure_password

# Prometheus
PROMETHEUS_RETENTION_TIME=30d
```

## Data Persistence

All data is persisted in Docker named volumes:

| Volume | Purpose |
|--------|---------|
| `ladon_prometheus_data` | Prometheus time-series database |
| `ladon_grafana_data` | Grafana dashboards and configuration |
| `ladon_arize_data` | Phoenix traces and ML observability |

Volumes survive container restarts. To completely reset:

```bash
docker compose down -v  # WARNING: Deletes all monitoring data
```

## ML Observability with Phoenix

Arize Phoenix provides ML model observability:

- **Trace Analysis** - LLM call traces and latency
- **Evaluation** - Model quality metrics
- **Embeddings** - Vector space visualization

### Instrumenting Your Application

```python
from phoenix.otel import register
from opentelemetry import trace

# Initialize Phoenix
tracer_provider = register(
    project_name="my-project",
    endpoint="http://localhost:4317"  # OTLP gRPC endpoint
)

# Your LLM calls will be automatically traced
```

## Troubleshooting

### GPU Metrics Not Available

1. Verify NVIDIA drivers:
   ```bash
   nvidia-smi
   ```

2. Check NVIDIA Container Toolkit:
   ```bash
   docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
   ```

3. Check DCGM exporter logs:
   ```bash
   docker logs dcgm-exporter
   ```

### Prometheus Not Scraping Targets

1. Check service health:
   ```bash
   docker compose ps
   ```

2. View Prometheus targets: http://localhost:9090/targets

3. Test connectivity:
   ```bash
   curl http://localhost:9400/metrics
   ```

### Grafana Dashboards Not Showing

1. Check Prometheus data source in Grafana
2. Verify Prometheus is running: http://localhost:9090
3. Run persistence fix if needed:
   ```bash
   python scripts/ensure_grafana_persistence.py
   ```

## Project Structure

```
LadonStack/
├── docker-compose.yml           # Main orchestration
├── monitoring.sh                # Management script
├── prometheus/
│   ├── prometheus.yml           # Scrape configuration
│   ├── alert_rules.yml          # Alert definitions
│   └── process-exporter.yml     # Process monitoring rules
├── grafana/
│   ├── grafana.ini              # Grafana configuration
│   └── provisioning/
│       ├── dashboards/          # Dashboard JSON files
│       └── datasources/         # Datasource configuration
├── arize/
│   └── pathrag-monitor/         # PathRAG visualization tool
├── graph-db-monitor/            # Graph database monitoring
├── scripts/                     # Utility scripts
│   ├── gpu_metrics_exporter.py
│   ├── backup_grafana_dashboards.py
│   └── ensure_grafana_persistence.py
├── infra/                       # Infrastructure configs
├── logs/                        # Application logs
└── backup/                      # Configuration backups
```

## Requirements

### System Requirements

- Docker 24.0+
- Docker Compose v2.20+
- NVIDIA Driver 525+
- NVIDIA Container Toolkit
- 4GB+ RAM (for monitoring stack)
- 10GB+ disk space (for metrics retention)

### Python Dependencies (for scripts)

```bash
pip install -r requirements.txt
```

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Test changes locally with `docker compose`
4. Submit a pull request

## Related Projects

- [DCGM](https://github.com/NVIDIA/DCGM) - NVIDIA Data Center GPU Manager
- [Prometheus](https://prometheus.io/) - Monitoring system
- [Grafana](https://grafana.com/) - Visualization platform
- [Arize Phoenix](https://github.com/Arize-ai/phoenix) - ML Observability

## Status

**Production Ready** - Actively maintained standalone monitoring stack.

Last update: November 2025
