# NVMe Drive Monitoring Setup

## Overview

Comprehensive NVMe monitoring system tracking temperature, I/O performance, and drive health metrics for all 4 NVMe drives in the system.

**Setup Date**: October 22, 2025

## Monitored Drives

| Device | Model | Capacity | Serial |
|--------|-------|----------|--------|
| nvme0 | CT4000T700SSD3 | 4.0 TB | 2409E89A3464 |
| nvme1 | CT1000T500SSD8 | 1.0 TB | 2415484C6FF5 |
| nvme2 | CT2000T700SSD3 | 2.0 TB | 2349E8878CDB |
| nvme3 | FIKWOT FX991 1TB | 1.0 TB | AA242830140 |

## Architecture

### Components

1. **nvme_exporter.py** (`scripts/nvme_exporter.py`)
   - Python script that collects NVMe SMART data every 30 seconds
   - Uses `nvme-cli` to query device health
   - Exports metrics in Prometheus text format
   - Runs as systemd service

2. **nvme-exporter.service** (`/etc/systemd/system/nvme-exporter.service`)
   - Systemd service running the exporter
   - Runs as root (required for nvme commands)
   - Writes to `/var/lib/node_exporter/nvme_metrics.prom`

3. **Node Exporter** (Docker container)
   - Mounts `/var/lib/node_exporter` directory
   - Textfile collector reads `*.prom` files
   - Exposes metrics on port 9100

4. **Prometheus** (Docker container)
   - Scrapes node-exporter every 15 seconds
   - Stores time-series data

5. **Grafana Dashboard** ("NVMe Drive Monitoring")
   - Visualizes all NVMe metrics
   - Includes temperature alerts
   - Shows health indicators table

## Collected Metrics

### Temperature
- `nvme_temperature_celsius` - Current drive temperature in °C
- Alert threshold: 70°C

### I/O Performance
- `nvme_data_units_read_total` - Total data read (512-byte units)
- `nvme_data_units_written_total` - Total data written (512-byte units)
- `nvme_host_read_commands_total` - Total read commands
- `nvme_host_write_commands_total` - Total write commands

Derived metrics:
- Read/Write rate (MB/s) calculated via `rate()` function
- Read/Write IOPS calculated from command totals

### Health Indicators
- `nvme_percentage_used` - Percentage of rated endurance used
- `nvme_available_spare_percent` - Available spare capacity
- `nvme_critical_warning` - Critical warning indicator (0=ok)
- `nvme_media_errors_total` - Media/data integrity errors
- `nvme_unsafe_shutdowns_total` - Count of unsafe shutdowns
- `nvme_power_on_hours_total` - Total power-on hours
- `nvme_power_cycles_total` - Total power cycles

## Dashboard Panels

1. **NVMe Temperatures** - Real-time temperature graph with alert
2. **Data Read (TB)** - Cumulative data read per drive
3. **Data Written (TB)** - Cumulative data written per drive
4. **Read Rate** - Current read throughput (MB/s)
5. **Write Rate** - Current write throughput (MB/s)
6. **Drive Health Indicators** - Table showing health metrics
7. **IOPS - Read Commands** - Read operations per second
8. **IOPS - Write Commands** - Write operations per second

## Service Management

### Check Service Status
```bash
sudo systemctl status nvme-exporter.service
```

### View Logs
```bash
sudo journalctl -u nvme-exporter.service -f
```

### Restart Service
```bash
sudo systemctl restart nvme-exporter.service
```

### Stop/Start Service
```bash
sudo systemctl stop nvme-exporter.service
sudo systemctl start nvme-exporter.service
```

### Disable/Enable Service
```bash
sudo systemctl disable nvme-exporter.service  # Don't start at boot
sudo systemctl enable nvme-exporter.service   # Start at boot
```

## Accessing the Dashboard

1. **Grafana**: http://localhost:3000
2. Navigate to Dashboards → Browse
3. Look for "NVMe Drive Monitoring" dashboard
4. Tags: `nvme`, `storage`, `health`

## Configuration

### Update Collection Interval

Edit `/etc/systemd/system/nvme-exporter.service`:
```ini
Environment="NVME_UPDATE_INTERVAL=60"  # Change to 60 seconds
```

Then reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart nvme-exporter.service
```

### Add/Remove Drives

The exporter auto-detects drives, but you can manually specify them in `scripts/nvme_exporter.py`:
```python
NVME_DEVICES = ["nvme0", "nvme1", "nvme2", "nvme3"]  # Edit this list
```

### Modify Alert Thresholds

Edit the dashboard JSON in `grafana/provisioning/dashboards/json/nvme-monitoring.json` and modify the alert configuration.

## Troubleshooting

### No Metrics Appearing

1. Check service is running:
   ```bash
   sudo systemctl status nvme-exporter.service
   ```

2. Verify metrics file exists and is recent:
   ```bash
   ls -la /var/lib/node_exporter/nvme_metrics.prom
   cat /var/lib/node_exporter/nvme_metrics.prom | head -20
   ```

3. Check node-exporter can see the file:
   ```bash
   docker exec node-exporter ls -la /node_exporter_metrics/
   docker exec node-exporter cat /node_exporter_metrics/nvme_metrics.prom | head
   ```

4. Verify metrics in Prometheus:
   ```bash
   curl -s http://localhost:9100/metrics | grep nvme_temperature
   curl -s http://localhost:9090/api/v1/query?query=nvme_temperature_celsius
   ```

### Permission Errors

The exporter runs as root because nvme commands require root access. If you see permission errors:

```bash
# Check nvme-cli is installed
which nvme

# Test nvme commands manually
sudo nvme list
sudo nvme smart-log /dev/nvme0
```

### Temperature Values Incorrect

Temperatures are automatically converted from Kelvin to Celsius in the exporter script. If values seem wrong, check the conversion logic in `scripts/nvme_exporter.py` at line ~310.

## Performance Impact

- **CPU Usage**: <0.1% average
- **Memory**: ~7-10 MB
- **Disk I/O**: Minimal (one file write every 30 seconds, ~6KB)
- **Network**: None (local only)

## Files Created/Modified

### New Files
- `/home/todd/olympus/Ladon/scripts/nvme_exporter.py`
- `/home/todd/olympus/Ladon/infra/nvme-exporter.service`
- `/home/todd/olympus/Ladon/grafana/provisioning/dashboards/json/nvme-monitoring.json`
- `/etc/systemd/system/nvme-exporter.service`
- `/var/lib/node_exporter/nvme_metrics.prom`

### Modified Files
- `/home/todd/olympus/Ladon/docker-compose.yml` - Updated node-exporter volume mounts

## Current Drive Status (at setup time)

Based on initial readings:

| Drive | Temp (°C) | Data Read (TB) | Data Written (TB) | Power Hours | Status |
|-------|-----------|----------------|-------------------|-------------|--------|
| nvme0 | 57 | 76.9 | 55.9 | 12,524 | Good |
| nvme1 | 38 | 9.5 | 3.3 | - | Good |
| nvme2 | 43 | 8.4 | 13.2 | - | Good |
| nvme3 | 40 | 20.2 | 8.3 | - | Good |

All drives show:
- ✓ 0% endurance used
- ✓ 100% available spare
- ✓ 0 critical warnings
- ✓ 0 media errors
- ✓ Temperatures normal (38-57°C)

## Maintenance

### Weekly
- Check dashboard for any temperature spikes
- Review media error counts
- Monitor endurance usage percentage

### Monthly
- Export metrics history
- Check for firmware updates
- Review total data written vs. endurance ratings

### Quarterly
- Verify all drives are detected
- Update nvme-cli if needed
- Review alert thresholds

## References

- NVMe Command Line Interface: https://github.com/linux-nvme/nvme-cli
- Prometheus Node Exporter Textfile Collector: https://github.com/prometheus/node_exporter
- NVMe SMART Attributes: NVMe 1.4 specification

## Notes

- The nvme0 drive (4TB Crucial T700) has significantly more usage than others (76.9TB read, 55.9TB written, 12,524 power-on hours)
- The nvme3 drive (FIKWOT) has the highest unsafe shutdown count (187) - monitor for stability issues
- All temperatures are within normal operating range for NVMe SSDs (typically rated to 70-85°C)
