# Grafana Configuration

This directory contains the Grafana configuration for the HADES monitoring stack.

## Directory Structure

- `custom.ini`: Main Grafana configuration file mounted to `/etc/grafana/grafana.ini`
- `provisioning/`: Provisioning configuration for dashboards and datasources
  - `dashboards/`: Dashboard provisioning configuration
    - `dashboard.yml`: Dashboard provider configuration
    - `json/`: Directory containing dashboard JSON files that will be loaded by Grafana
  - `datasources/`: Datasource provisioning configuration
    - `datasource.yml`: Datasource configuration for Prometheus

## Backup Strategy

When making changes to dashboards in the Grafana UI:
1. Export the dashboard JSON (Dashboard settings → JSON Model)
2. Save the JSON file to `provisioning/dashboards/json/`
3. Commit the changes to Git

This ensures that dashboard changes are properly version-controlled and can be restored if needed.
