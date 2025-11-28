#!/usr/bin/env python3
"""
NVMe SMART Metrics Exporter for Prometheus
Collects temperature, I/O stats, health metrics from NVMe drives
Outputs to textfile for node_exporter collection
"""

import subprocess
import json
import re
import time
import os
from pathlib import Path
from typing import Dict, List, Optional

# Configuration
METRICS_DIR = Path(os.getenv("METRICS_DIR", "/var/lib/node_exporter"))
UPDATE_INTERVAL = int(os.getenv("NVME_UPDATE_INTERVAL", "30"))  # seconds
NVME_DEVICES = ["nvme0", "nvme1", "nvme2", "nvme3"]  # Auto-detect if empty


def run_command(cmd: List[str]) -> Optional[str]:
    """Execute command and return output"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running {' '.join(cmd)}: {e}")
        return None
    except subprocess.TimeoutExpired:
        print(f"Timeout running {' '.join(cmd)}")
        return None


def detect_nvme_devices() -> List[str]:
    """Auto-detect NVMe devices"""
    output = run_command(["nvme", "list", "-o", "json"])
    if not output:
        return []

    try:
        data = json.loads(output)
        devices = []
        for device in data.get("Devices", []):
            node = device.get("DevicePath", "")
            if node.startswith("/dev/nvme"):
                # Extract nvme0, nvme1, etc
                match = re.search(r'(nvme\d+)', node)
                if match:
                    devices.append(match.group(1))
        return sorted(set(devices))
    except json.JSONDecodeError:
        print("Failed to parse nvme list output")
        return []


def get_nvme_smart(device: str) -> Optional[Dict]:
    """Get SMART data for NVMe device"""
    output = run_command(["nvme", "smart-log", f"/dev/{device}", "-o", "json"])
    if not output:
        return None

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        print(f"Failed to parse SMART data for {device}")
        return None


def get_nvme_info(device: str) -> Optional[Dict]:
    """Get device info (model, serial)"""
    output = run_command(["nvme", "id-ctrl", f"/dev/{device}", "-o", "json"])
    if not output:
        return None

    try:
        data = json.loads(output)
        return {
            "model": data.get("mn", "").strip(),
            "serial": data.get("sn", "").strip(),
            "firmware": data.get("fr", "").strip()
        }
    except json.JSONDecodeError:
        print(f"Failed to parse device info for {device}")
        return None


def get_iostat(device: str) -> Optional[Dict]:
    """Get current I/O statistics from /proc/diskstats"""
    try:
        with open("/proc/diskstats", "r") as f:
            for line in f:
                fields = line.split()
                if len(fields) >= 14 and fields[2] == f"{device}n1":
                    return {
                        "reads_completed": int(fields[3]),
                        "reads_merged": int(fields[4]),
                        "sectors_read": int(fields[5]),
                        "time_reading_ms": int(fields[6]),
                        "writes_completed": int(fields[7]),
                        "writes_merged": int(fields[8]),
                        "sectors_written": int(fields[9]),
                        "time_writing_ms": int(fields[10]),
                        "io_in_progress": int(fields[11]),
                        "time_io_ms": int(fields[12]),
                        "weighted_time_io_ms": int(fields[13])
                    }
    except Exception as e:
        print(f"Failed to read iostat for {device}: {e}")
    return None


def format_prometheus_metrics(metrics: Dict[str, List[Dict]]) -> str:
    """Format metrics in Prometheus text format"""
    lines = []
    timestamp = int(time.time() * 1000)

    # Temperature metrics
    lines.append("# HELP nvme_temperature_celsius Current temperature of NVMe device in Celsius")
    lines.append("# TYPE nvme_temperature_celsius gauge")
    for device, data in metrics.items():
        if data and "temperature" in data[0]:
            temp = data[0]["temperature"]
            model = data[0].get("model", "unknown")
            serial = data[0].get("serial", "unknown")
            lines.append(
                f'nvme_temperature_celsius{{device="{device}",model="{model}",serial="{serial}"}} {temp}'
            )

    # Available spare percentage
    lines.append("# HELP nvme_available_spare_percent Available spare capacity percentage")
    lines.append("# TYPE nvme_available_spare_percent gauge")
    for device, data in metrics.items():
        if data and "available_spare" in data[0]:
            spare = data[0]["available_spare"]
            model = data[0].get("model", "unknown")
            serial = data[0].get("serial", "unknown")
            lines.append(
                f'nvme_available_spare_percent{{device="{device}",model="{model}",serial="{serial}"}} {spare}'
            )

    # Percentage used
    lines.append("# HELP nvme_percentage_used Percentage of rated endurance used")
    lines.append("# TYPE nvme_percentage_used gauge")
    for device, data in metrics.items():
        if data and "percentage_used" in data[0]:
            used = data[0]["percentage_used"]
            model = data[0].get("model", "unknown")
            serial = data[0].get("serial", "unknown")
            lines.append(
                f'nvme_percentage_used{{device="{device}",model="{model}",serial="{serial}"}} {used}'
            )

    # Critical warning
    lines.append("# HELP nvme_critical_warning Critical warning indicator (0=ok, >0=warning)")
    lines.append("# TYPE nvme_critical_warning gauge")
    for device, data in metrics.items():
        if data and "critical_warning" in data[0]:
            warning = data[0]["critical_warning"]
            model = data[0].get("model", "unknown")
            serial = data[0].get("serial", "unknown")
            lines.append(
                f'nvme_critical_warning{{device="{device}",model="{model}",serial="{serial}"}} {warning}'
            )

    # Data units read (512-byte units)
    lines.append("# HELP nvme_data_units_read_total Total data units read (512-byte units)")
    lines.append("# TYPE nvme_data_units_read_total counter")
    for device, data in metrics.items():
        if data and "data_units_read" in data[0]:
            units = data[0]["data_units_read"]
            model = data[0].get("model", "unknown")
            serial = data[0].get("serial", "unknown")
            lines.append(
                f'nvme_data_units_read_total{{device="{device}",model="{model}",serial="{serial}"}} {units}'
            )

    # Data units written (512-byte units)
    lines.append("# HELP nvme_data_units_written_total Total data units written (512-byte units)")
    lines.append("# TYPE nvme_data_units_written_total counter")
    for device, data in metrics.items():
        if data and "data_units_written" in data[0]:
            units = data[0]["data_units_written"]
            model = data[0].get("model", "unknown")
            serial = data[0].get("serial", "unknown")
            lines.append(
                f'nvme_data_units_written_total{{device="{device}",model="{model}",serial="{serial}"}} {units}'
            )

    # Host read commands
    lines.append("# HELP nvme_host_read_commands_total Total host read commands")
    lines.append("# TYPE nvme_host_read_commands_total counter")
    for device, data in metrics.items():
        if data and "host_read_commands" in data[0]:
            cmds = data[0]["host_read_commands"]
            model = data[0].get("model", "unknown")
            serial = data[0].get("serial", "unknown")
            lines.append(
                f'nvme_host_read_commands_total{{device="{device}",model="{model}",serial="{serial}"}} {cmds}'
            )

    # Host write commands
    lines.append("# HELP nvme_host_write_commands_total Total host write commands")
    lines.append("# TYPE nvme_host_write_commands_total counter")
    for device, data in metrics.items():
        if data and "host_write_commands" in data[0]:
            cmds = data[0]["host_write_commands"]
            model = data[0].get("model", "unknown")
            serial = data[0].get("serial", "unknown")
            lines.append(
                f'nvme_host_write_commands_total{{device="{device}",model="{model}",serial="{serial}"}} {cmds}'
            )

    # Power on hours
    lines.append("# HELP nvme_power_on_hours_total Total power-on hours")
    lines.append("# TYPE nvme_power_on_hours_total counter")
    for device, data in metrics.items():
        if data and "power_on_hours" in data[0]:
            hours = data[0]["power_on_hours"]
            model = data[0].get("model", "unknown")
            serial = data[0].get("serial", "unknown")
            lines.append(
                f'nvme_power_on_hours_total{{device="{device}",model="{model}",serial="{serial}"}} {hours}'
            )

    # Power cycles
    lines.append("# HELP nvme_power_cycles_total Total power cycles")
    lines.append("# TYPE nvme_power_cycles_total counter")
    for device, data in metrics.items():
        if data and "power_cycles" in data[0]:
            cycles = data[0]["power_cycles"]
            model = data[0].get("model", "unknown")
            serial = data[0].get("serial", "unknown")
            lines.append(
                f'nvme_power_cycles_total{{device="{device}",model="{model}",serial="{serial}"}} {cycles}'
            )

    # Unsafe shutdowns
    lines.append("# HELP nvme_unsafe_shutdowns_total Total unsafe shutdowns")
    lines.append("# TYPE nvme_unsafe_shutdowns_total counter")
    for device, data in metrics.items():
        if data and "unsafe_shutdowns" in data[0]:
            shutdowns = data[0]["unsafe_shutdowns"]
            model = data[0].get("model", "unknown")
            serial = data[0].get("serial", "unknown")
            lines.append(
                f'nvme_unsafe_shutdowns_total{{device="{device}",model="{model}",serial="{serial}"}} {shutdowns}'
            )

    # Media errors
    lines.append("# HELP nvme_media_errors_total Total media errors")
    lines.append("# TYPE nvme_media_errors_total counter")
    for device, data in metrics.items():
        if data and "media_errors" in data[0]:
            errors = data[0]["media_errors"]
            model = data[0].get("model", "unknown")
            serial = data[0].get("serial", "unknown")
            lines.append(
                f'nvme_media_errors_total{{device="{device}",model="{model}",serial="{serial}"}} {errors}'
            )

    # I/O in progress
    lines.append("# HELP nvme_io_in_progress Current I/O operations in progress")
    lines.append("# TYPE nvme_io_in_progress gauge")
    for device, data in metrics.items():
        if data and "io_in_progress" in data[0]:
            io_prog = data[0]["io_in_progress"]
            model = data[0].get("model", "unknown")
            serial = data[0].get("serial", "unknown")
            lines.append(
                f'nvme_io_in_progress{{device="{device}",model="{model}",serial="{serial}"}} {io_prog}'
            )

    return "\n".join(lines) + "\n"


def collect_metrics() -> Dict[str, List[Dict]]:
    """Collect all NVMe metrics"""
    devices = NVME_DEVICES if NVME_DEVICES else detect_nvme_devices()
    if not devices:
        print("No NVMe devices found")
        return {}

    metrics = {}
    for device in devices:
        print(f"Collecting metrics for {device}")

        # Get device info
        info = get_nvme_info(device)
        if not info:
            continue

        # Get SMART data
        smart = get_nvme_smart(device)
        if not smart:
            continue

        # Get I/O stats
        iostat = get_iostat(device)

        # Combine all data
        # Note: temperature is in Kelvin, convert to Celsius
        temp_kelvin = smart.get("temperature", 0)
        temp_celsius = temp_kelvin - 273 if temp_kelvin > 0 else 0

        combined = {
            "model": info["model"],
            "serial": info["serial"],
            "firmware": info["firmware"],
            "temperature": temp_celsius,
            "critical_warning": smart.get("critical_warning", 0),
            "available_spare": smart.get("available_spare", 0),
            "percentage_used": smart.get("percentage_used", 0),
            "data_units_read": smart.get("data_units_read", 0),
            "data_units_written": smart.get("data_units_written", 0),
            "host_read_commands": smart.get("host_read_commands", 0),
            "host_write_commands": smart.get("host_write_commands", 0),
            "power_on_hours": smart.get("power_on_hours", 0),
            "power_cycles": smart.get("power_cycles", 0),
            "unsafe_shutdowns": smart.get("unsafe_shutdowns", 0),
            "media_errors": smart.get("media_errors", 0),
        }

        if iostat:
            combined.update(iostat)

        metrics[device] = [combined]

    return metrics


def write_metrics(metrics: Dict[str, List[Dict]], output_file: Path):
    """Write metrics to file atomically"""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    content = format_prometheus_metrics(metrics)

    # Write atomically
    temp_file = output_file.with_suffix(".tmp")
    temp_file.write_text(content)
    temp_file.rename(output_file)

    print(f"Metrics written to {output_file}")


def main():
    """Main collection loop"""
    output_file = METRICS_DIR / "nvme_metrics.prom"

    print(f"NVMe Exporter starting...")
    print(f"Output: {output_file}")
    print(f"Update interval: {UPDATE_INTERVAL}s")

    while True:
        try:
            metrics = collect_metrics()
            if metrics:
                write_metrics(metrics, output_file)
            else:
                print("No metrics collected")
        except Exception as e:
            print(f"Error collecting metrics: {e}")
            import traceback
            traceback.print_exc()

        time.sleep(UPDATE_INTERVAL)


if __name__ == "__main__":
    main()
