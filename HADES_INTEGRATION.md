# HADES Monitoring Integration Guide

This document explains how to integrate HADES component monitoring with the ladon monitoring stack.

## Overview

The HADES system exposes unified metrics for all components through a single FastAPI endpoint (`/metrics`). This endpoint automatically discovers and collects metrics from:

- **DocProc Components**: Document processing metrics (docling, core)
- **Model Engine Components**: AI model serving metrics (haystack) 
- **Embedding Components**: Embedding generation metrics (cpu, gpu, encoder)
- **Chunking Components**: Text chunking metrics (cpu, chonky, text, code)
- **Graph Enhancement**: ISNE and graph processing metrics
- **Storage Components**: Database and vector storage metrics
- **API Server**: FastAPI server performance metrics

## Integration Options

### Option 1: Host Networking (Development)

**Use Case**: Quick development setup, testing, single-machine deployment

**Setup:**
1. Start ladon monitoring stack:
   ```bash
   cd /home/todd/ML-Lab/Olympus/ladon
   ./monitoring.sh start
   ```

2. Start HADES with host networking:
   ```bash
   cd /home/todd/ML-Lab/Olympus/HADES
   poetry run uvicorn src.api.server:app --host 0.0.0.0 --port 8000
   ```

3. Update Prometheus configuration:
   ```yaml
   # In prometheus/prometheus.yml, change:
   - targets: ['hades:8000']
   # To:
   - targets: ['localhost:8000']
   ```

**Pros**: Simple setup, no Docker network configuration needed
**Cons**: Less isolation, not suitable for production

### Option 2: Docker Network (Recommended)

**Use Case**: Production deployment, container isolation, multi-service setup

**Setup:**
1. Start ladon monitoring stack (creates `hades-monitoring` network):
   ```bash
   cd /home/todd/ML-Lab/Olympus/ladon
   ./monitoring.sh start
   ```

2. Start HADES container on monitoring network:
   ```bash
   cd /home/todd/ML-Lab/Olympus/HADES
   
   # If using Docker directly:
   docker run --name hades-api \\
     --network hades-monitoring \\
     -p 8000:8000 \\
     hades:latest
   
   # If using docker-compose, add to HADES docker-compose.yml:
   networks:
     default:
       external:
         name: hades-monitoring
   ```

3. Prometheus will automatically scrape `hades:8000/metrics`

**Pros**: Proper isolation, production-ready, scalable
**Cons**: Requires Docker network management

### Option 3: External Service Discovery

**Use Case**: HADES running on different machine/cluster

**Setup:**
1. Update Prometheus configuration with HADES machine IP:
   ```yaml
   - job_name: 'hades-api'
     static_configs:
       - targets: ['<HADES_IP>:8000']
   ```

2. Ensure firewall allows Prometheus to reach HADES on port 8000

## Testing the Integration

### 1. Verify HADES Metrics Endpoint

```bash
# Test metrics endpoint directly
curl http://localhost:8000/metrics

# Expected output: Prometheus-formatted metrics
# Example metrics:
# hades_component_uptime_seconds{component="docling"} 123.45
# hades_component_documents_total{component="docling"} 42
# hades_model_engine_requests_total{component="haystack"} 156
```

### 2. Verify Prometheus Scraping

1. Open Prometheus UI: http://localhost:9090
2. Go to Status → Targets
3. Verify `hades-api` target shows as "UP"
4. Query metrics: Search for `hades_` in the query box

### 3. Verify Grafana Integration

1. Open Grafana: http://localhost:3000 (admin/admin)
2. Go to Explore
3. Select Prometheus data source
4. Query HADES metrics: `hades_component_uptime_seconds`

## Available HADES Metrics

### Component Infrastructure Metrics
- `hades_component_uptime_seconds{component="<name>"}` - Component uptime
- `hades_component_memory_rss_mb{component="<name>"}` - Memory usage
- `hades_component_supported_formats{component="<name>"}` - Supported formats count

### Component Performance Metrics
- `hades_component_documents_total{component="<name>"}` - Total documents processed
- `hades_component_documents_successful_total{component="<name>"}` - Successful documents
- `hades_component_documents_failed_total{component="<name>"}` - Failed documents
- `hades_component_success_rate_percent{component="<name>"}` - Success rate percentage
- `hades_component_documents_per_second{component="<name>"}` - Processing rate
- `hades_component_avg_processing_time_seconds{component="<name>"}` - Average processing time

### Format-Specific Metrics
- `hades_component_format_count{component="<name>",format="<format>"}` - Documents by format

### API Server Metrics
- `hades_api_uptime_seconds{service="hades-api"}` - API server uptime
- `hades_api_memory_rss_mb{service="hades-api"}` - API server memory usage
- `hades_api_status{service="hades-api"}` - API server status (1=up, 0=down)

## Creating Grafana Dashboards

### Basic Component Status Dashboard

1. Create new dashboard in Grafana
2. Add panels for:
   - **Component Status**: `hades_component_uptime_seconds > 0`
   - **Processing Rate**: `rate(hades_component_documents_total[5m])`
   - **Success Rate**: `hades_component_success_rate_percent`
   - **Memory Usage**: `hades_component_memory_rss_mb`

### Example Panel Queries

```promql
# Component uptime (shows which components are running)
hades_component_uptime_seconds

# Document processing rate (docs per second, 5min average)
rate(hades_component_documents_total[5m])

# Error rate by component
rate(hades_component_documents_failed_total[5m])

# Memory usage trend
hades_component_memory_rss_mb

# Format distribution (pie chart)
sum by (format) (hades_component_format_count)
```

## Troubleshooting

### HADES Target Shows as DOWN

1. **Check network connectivity**:
   ```bash
   # From ladon container
   docker exec prometheus curl http://hades:8000/metrics
   
   # From host
   curl http://localhost:8000/metrics
   ```

2. **Verify Docker network**:
   ```bash
   docker network ls | grep hades-monitoring
   docker network inspect hades-monitoring
   ```

3. **Check HADES logs**:
   ```bash
   # If running via Poetry
   poetry run python -m src.api.server
   
   # If running via Docker
   docker logs hades-api
   ```

### No Metrics Appearing

1. **Check HADES component registration**:
   ```bash
   # Test component discovery
   python test_api_metrics.py
   ```

2. **Verify metrics format**:
   ```bash
   curl http://localhost:8000/metrics | head -20
   ```

3. **Check Prometheus configuration**:
   ```bash
   # Reload Prometheus config
   curl -X POST http://localhost:9090/-/reload
   ```

### Component Metrics Missing

1. **Check component initialization**:
   - Components must be registered in the global registry
   - Components must implement `export_metrics_prometheus()` method

2. **Check component errors**:
   - Review HADES API logs for component instantiation errors
   - Some abstract components may fail to instantiate (this is normal)

## Production Considerations

### Security
- Use authentication for Prometheus endpoints in production
- Restrict network access to monitoring ports
- Consider TLS for metrics endpoints

### Performance
- Monitor Prometheus storage usage with large numbers of metrics
- Adjust scrape intervals based on monitoring needs
- Use metric aggregation for high-cardinality data

### Reliability
- Set up Prometheus federation for high availability
- Configure alerting for HADES component failures
- Implement backup strategies for Grafana dashboards

## Next Steps

1. **Start both systems** using your preferred integration option
2. **Create custom dashboards** specific to your HADES workflows
3. **Set up alerting rules** for component failures and performance issues
4. **Extend metrics** by adding custom metrics to HADES components as needed

The integration provides a solid foundation for monitoring HADES components alongside system metrics collected by the ladon stack.