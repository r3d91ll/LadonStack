# Monitoring Stack Rebuild - October 22, 2025

## Summary

Successfully migrated monitoring infrastructure from conveyance-framework to the dedicated Ladon monitoring stack. All dashboards are now properly persisted and accessible.

## What Was Done

### 1. Backed Up Conveyance-Framework Configuration
- Created backup directory: `/home/todd/olympus/Ladon/backup/conveyance-grafana-20251022/`
- Backed up all Grafana configs, dashboards, and database
- Preserved datasource configurations

### 2. Migrated Dashboards
- Copied conveyance dashboards to Ladon provisioning directory
- Existing Ladon dashboards preserved:
  - Node Exporter Full (system metrics)
  - NVIDIA RTX A6000 GPU Monitoring
  - Real-Time GPU Metrics

### 3. Tore Down Old Stack
- Stopped and removed conveyance-framework monitoring containers:
  - conveyance-grafana
  - conveyance-phoenix
  - conveyance-postgres-exporter
  - conveyance-cadvisor
  - conveyance-prometheus
  - conveyance-node-exporter

### 4. Started Ladon Monitoring Stack
- All services running via docker-compose from `/home/todd/olympus/Ladon`
- New volumes created with `ladon_` prefix:
  - `ladon_grafana_data` - Grafana database and configuration
  - `ladon_prometheus_data` - Prometheus time-series data
  - `ladon_arize_data` - Phoenix ML monitoring data

## Services Status

### Running Successfully ✓
- **Grafana** (port 3000) - Dashboard and visualization
- **Prometheus** (port 9090) - Metrics collection
- **Node Exporter** (port 9100) - System metrics
- **Process Exporter** (port 9256) - Process metrics
- **Arize Phoenix** (port 8084) - ML observability

### Needs Attention ⚠
- **DCGM Exporter** - Failing with NVML initialization error
  - Error: "Failed to initialize NVML"
  - Issue: Library path mismatch in docker-compose.yml line 31
  - Current: `/usr/lib/x86_64-linux-gnu/libnvidia-ml.so.575.57.08`
  - Need to verify actual NVIDIA library version on host

## Dashboard Persistence

✓ **Verified**: Dashboards persist across container restarts
- Dashboards stored in: `/var/lib/docker/volumes/ladon_grafana_data/_data`
- Provisioned dashboards auto-loaded from: `/home/todd/olympus/Ladon/grafana/provisioning/dashboards/json/`

## Access Information

- **Grafana**: http://localhost:3000
  - Username: admin
  - Password: admin
- **Prometheus**: http://localhost:9090
- **Arize Phoenix**: http://localhost:8084

## Files Disabled

The following conveyance dashboards were disabled due to format issues:
- `conveyance-performance.json.disabled`
- `frontend-monitoring.json.disabled`

These can be fixed and re-enabled if needed. They're backed up in the backup directory.

## Next Steps

1. **Fix DCGM Exporter**: Update nvidia library path in docker-compose.yml
   ```bash
   # Find correct library version
   ls -la /usr/lib/x86_64-linux-gnu/libnvidia-ml.so*
   # Update docker-compose.yml line 31 with correct path
   ```

2. **Optional**: Fix and re-enable conveyance dashboards if metrics are available

3. **Verify GPU Metrics**: Once DCGM is working, check GPU dashboards have data

## Backup Location

All original conveyance-framework Grafana configuration backed up to:
`/home/todd/olympus/Ladon/backup/conveyance-grafana-20251022/`
