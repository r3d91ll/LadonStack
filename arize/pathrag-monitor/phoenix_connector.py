#!/usr/bin/env python3
"""
PathRAG Monitor - Phoenix Connector

This module provides functions to connect to Arize Phoenix and retrieve trace data
from the PathRAG project.
"""

import os
import requests
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Default Phoenix settings - can be overridden with environment variables
PHOENIX_HOST = os.environ.get("PHOENIX_HOST", "localhost")
PHOENIX_PORT = os.environ.get("PHOENIX_PORT", "8084")
PHOENIX_URL = f"http://{PHOENIX_HOST}:{PHOENIX_PORT}"
PHOENIX_UI_URL = f"http://{PHOENIX_HOST}:{PHOENIX_PORT}"

# Use PHOENIX_INFERENCE_PROJECT_NAME if available, otherwise fall back to PHOENIX_PROJECT_NAME
PHOENIX_PROJECT = os.environ.get("PHOENIX_INFERENCE_PROJECT_NAME", 
                              os.environ.get("PHOENIX_PROJECT_NAME", "pathrag-inference"))

print(f"🔍 Phoenix connector using project: {PHOENIX_PROJECT}")
print(f"🔍 Phoenix API URL: {PHOENIX_URL}")
print(f"🔍 Phoenix UI URL: {PHOENIX_UI_URL}")

def check_phoenix_connection() -> bool:
    """
    Check if Phoenix is running and accessible
    
    Returns:
        bool: True if Phoenix is running, False otherwise
    """
    try:
        response = requests.get(f"{PHOENIX_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def get_phoenix_projects() -> List[str]:
    """
    Get list of projects in Phoenix
    
    Returns:
        List[str]: List of project names
    """
    try:
        response = requests.get(f"{PHOENIX_URL}/api/projects")
        if response.status_code == 200:
            data = response.json()
            return [project["name"] for project in data.get("projects", [])]
        return []
    except Exception:
        return []

def get_traces(project_name: str = PHOENIX_PROJECT, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get traces from Phoenix for a specific project
    
    Args:
        project_name: Name of the Phoenix project
        limit: Maximum number of traces to retrieve
        
    Returns:
        List[Dict[str, Any]]: List of trace data
    """
    try:
        response = requests.get(f"{PHOENIX_URL}/api/projects/{project_name}/traces?limit={limit}")
        if response.status_code == 200:
            data = response.json()
            return data.get("traces", [])
        return []
    except Exception:
        return []

def get_trace_details(project_name: str, trace_id: str) -> Optional[Dict[str, Any]]:
    """
    Get details for a specific trace
    
    Args:
        project_name: Name of the Phoenix project
        trace_id: ID of the trace to retrieve
        
    Returns:
        Optional[Dict[str, Any]]: Trace details or None if not found
    """
    try:
        response = requests.get(f"{PHOENIX_URL}/api/projects/{project_name}/traces/{trace_id}")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

def get_path_metrics(project_name: str = PHOENIX_PROJECT, 
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None,
                    limit: int = 100) -> pd.DataFrame:
    """
    Get path metrics from Phoenix traces and convert to DataFrame
    
    Args:
        project_name: Name of the Phoenix project
        start_date: Start date for filtering traces
        end_date: End date for filtering traces
        limit: Maximum number of traces to retrieve
        
    Returns:
        pd.DataFrame: DataFrame containing path metrics
    """
    traces = get_traces(project_name, limit)
    
    # Extract relevant metrics from traces
    metrics_data = []
    for trace in traces:
        trace_id = trace.get("id")
        timestamp = trace.get("timestamp")
        
        # Get detailed trace data
        details = get_trace_details(project_name, trace_id)
        if not details:
            continue
            
        # Extract path metrics from trace details
        spans = details.get("spans", [])
        path_spans = [s for s in spans if "path" in s.get("name", "").lower()]
        
        for span in path_spans:
            path_metrics = {
                "trace_id": trace_id,
                "timestamp": timestamp,
                "path_id": span.get("id"),
                "path_name": span.get("name"),
                "latency_ms": span.get("duration_ms", 0),
            }
            
            # Extract attributes
            attributes = span.get("attributes", {})
            path_metrics.update({
                "path_length": attributes.get("path.length", 0),
                "path_score": attributes.get("path.score", 0),
                "nodes_visited": attributes.get("path.nodes_visited", 0),
                "edges_traversed": attributes.get("path.edges_traversed", 0),
                "pruning_efficiency": attributes.get("path.pruning_efficiency", 0),
                "path_nodes": attributes.get("path.nodes", "[]"),
                "query": attributes.get("query.text", ""),
            })
            
            metrics_data.append(path_metrics)
    
    # Convert to DataFrame
    if not metrics_data:
        return pd.DataFrame()
        
    df = pd.DataFrame(metrics_data)
    
    # Convert timestamp to datetime
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        # Filter by date range if provided
        if start_date:
            df = df[df["timestamp"] >= pd.Timestamp(start_date)]
        if end_date:
            df = df[df["timestamp"] <= pd.Timestamp(end_date)]
    
    return df

if __name__ == "__main__":
    # Test the Phoenix connection
    if check_phoenix_connection():
        print(f"✅ Connected to Phoenix at {PHOENIX_URL}")
        
        # Get projects
        projects = get_phoenix_projects()
        print(f"Found {len(projects)} projects: {', '.join(projects)}")
        
        # Get traces for PathRAG project
        if PHOENIX_PROJECT in projects:
            traces = get_traces(PHOENIX_PROJECT, limit=5)
            print(f"Found {len(traces)} traces in {PHOENIX_PROJECT} project")
            
            # Get path metrics
            metrics_df = get_path_metrics(PHOENIX_PROJECT, limit=5)
            print(f"Extracted {len(metrics_df)} path metrics")
            if not metrics_df.empty:
                print(metrics_df.head())
        else:
            print(f"Project {PHOENIX_PROJECT} not found in Phoenix")
    else:
        print(f"❌ Failed to connect to Phoenix at {PHOENIX_URL}")
