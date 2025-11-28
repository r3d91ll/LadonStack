#!/usr/bin/env python3
"""
Test script for HADES-ladon monitoring integration.

This script tests the connectivity and configuration between HADES and ladon monitoring stack.
"""

import requests
import yaml
import json
import time
from pathlib import Path

def test_prometheus_config():
    """Test the Prometheus configuration for HADES integration."""
    print("="*60)
    print("Testing Prometheus Configuration")
    print("="*60)
    
    try:
        # Read prometheus.yml
        prometheus_config_path = Path("prometheus/prometheus.yml")
        if not prometheus_config_path.exists():
            print("❌ prometheus.yml not found")
            return False
        
        with open(prometheus_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check for HADES job
        scrape_configs = config.get('scrape_configs', [])
        hades_jobs = [job for job in scrape_configs if 'hades' in job.get('job_name', '')]
        
        if not hades_jobs:
            print("❌ No HADES jobs found in Prometheus configuration")
            return False
        
        print(f"✓ Found {len(hades_jobs)} HADES job(s) in Prometheus config:")
        for job in hades_jobs:
            job_name = job.get('job_name')
            targets = job.get('static_configs', [{}])[0].get('targets', [])
            metrics_path = job.get('metrics_path', '/metrics')
            scrape_interval = job.get('scrape_interval', 'default')
            
            print(f"  - Job: {job_name}")
            print(f"    Targets: {targets}")
            print(f"    Metrics path: {metrics_path}")
            print(f"    Scrape interval: {scrape_interval}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading Prometheus config: {e}")
        return False


def test_hades_connectivity():
    """Test connectivity to HADES metrics endpoint."""
    print("\n" + "="*60)
    print("Testing HADES Connectivity")
    print("="*60)
    
    # Test different possible endpoints
    endpoints = [
        "http://localhost:8000/metrics",
        "http://hades:8000/metrics",
        "http://127.0.0.1:8000/metrics"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\nTesting {endpoint}...")
            response = requests.get(endpoint, timeout=5)
            
            if response.status_code == 200:
                content = response.text
                print(f"✓ SUCCESS: {endpoint}")
                print(f"  Status: {response.status_code}")
                print(f"  Content-Type: {response.headers.get('content-type', 'unknown')}")
                print(f"  Content length: {len(content)} characters")
                
                # Check for Prometheus format
                lines = content.strip().split('\n')
                metric_lines = [line for line in lines if line and not line.startswith('#')]
                print(f"  Metric lines: {len(metric_lines)}")
                
                # Show sample metrics
                if metric_lines:
                    print("  Sample metrics:")
                    for line in metric_lines[:3]:
                        print(f"    {line}")
                
                return True, endpoint
                
            else:
                print(f"❌ FAILED: {endpoint} - Status {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ FAILED: {endpoint} - Connection refused")
        except requests.exceptions.Timeout:
            print(f"❌ FAILED: {endpoint} - Timeout")
        except Exception as e:
            print(f"❌ FAILED: {endpoint} - Error: {e}")
    
    return False, None


def test_prometheus_targets():
    """Test Prometheus targets endpoint."""
    print("\n" + "="*60)
    print("Testing Prometheus Targets")
    print("="*60)
    
    try:
        # Test Prometheus API
        prometheus_url = "http://localhost:9090/api/v1/targets"
        response = requests.get(prometheus_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            targets = data.get('data', {}).get('activeTargets', [])
            
            print(f"✓ Prometheus API accessible")
            print(f"✓ Found {len(targets)} active targets")
            
            # Look for HADES targets
            hades_targets = [t for t in targets if 'hades' in t.get('job', '').lower()]
            
            if hades_targets:
                print(f"✓ Found {len(hades_targets)} HADES target(s):")
                for target in hades_targets:
                    job = target.get('job')
                    endpoint = target.get('scrapeUrl')
                    health = target.get('health')
                    last_error = target.get('lastError', 'None')
                    
                    print(f"  - Job: {job}")
                    print(f"    Endpoint: {endpoint}")
                    print(f"    Health: {health}")
                    if last_error != 'None':
                        print(f"    Last Error: {last_error}")
            else:
                print("❌ No HADES targets found in Prometheus")
                print("Available targets:")
                for target in targets[:5]:  # Show first 5 targets
                    print(f"  - {target.get('job')}: {target.get('scrapeUrl')}")
            
            return True
            
        else:
            print(f"❌ Prometheus API not accessible - Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Prometheus: {e}")
        return False


def main():
    """Run all integration tests."""
    print("HADES-Ladon Monitoring Integration Test")
    print("=" * 60)
    
    results = []
    
    # Test 1: Prometheus configuration
    config_ok = test_prometheus_config()
    results.append(("Prometheus Config", config_ok))
    
    # Test 2: HADES connectivity
    hades_ok, working_endpoint = test_hades_connectivity()
    results.append(("HADES Connectivity", hades_ok))
    
    # Test 3: Prometheus targets (only if Prometheus is running)
    prometheus_ok = test_prometheus_targets()
    results.append(("Prometheus Targets", prometheus_ok))
    
    # Summary
    print("\n" + "="*60)
    print("Integration Test Summary")
    print("="*60)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print(f"\n🎉 All tests passed! Integration ready.")
        if working_endpoint:
            print(f"HADES metrics available at: {working_endpoint}")
    else:
        print(f"\n⚠️  Some tests failed. Check configuration and connectivity.")
        print("\nNext steps:")
        print("1. Start HADES API server: poetry run python -m src.api.server")
        print("2. Start ladon monitoring: ./monitoring.sh start")
        print("3. Check network connectivity between services")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())