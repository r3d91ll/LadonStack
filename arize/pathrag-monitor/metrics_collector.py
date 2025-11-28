#!/usr/bin/env python3
"""
PathRAG Monitor - Metrics Collector

This module handles loading, processing, and querying metrics data from PathRAG.
It provides functions to access path traversal metrics stored in SQLite or JSON format.
"""

import pandas as pd
import json
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from sqlitedict import SqliteDict
import networkx as nx
from typing import Dict, List, Tuple, Any, Optional

# Default paths - can be overridden with environment variables
DEFAULT_METRICS_DB = os.environ.get(
    "PATHRAG_METRICS_DB", 
    str(Path.home() / "ML-Lab/New-HADES/data/pathrag/metrics/path_metrics.sqlite")
)
DEFAULT_LOGS_DIR = os.environ.get(
    "PATHRAG_LOGS_DIR",
    str(Path.home() / "ML-Lab/New-HADES/data/pathrag/logs")
)

class PathRAGMetricsCollector:
    """Class to collect and process PathRAG metrics data"""
    
    def __init__(self, metrics_db: str = DEFAULT_METRICS_DB, logs_dir: str = DEFAULT_LOGS_DIR):
        """
        Initialize the metrics collector
        
        Args:
            metrics_db: Path to SQLite database for metrics
            logs_dir: Directory containing JSON log files
        """
        self.metrics_db = metrics_db
        self.logs_dir = logs_dir
        
        # Create metrics db directory if it doesn't exist
        os.makedirs(os.path.dirname(metrics_db), exist_ok=True)
    
    def load_metrics(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Load metrics data for the specified date range
        
        Args:
            start_date: Start date for filtering metrics
            end_date: End date for filtering metrics
            
        Returns:
            DataFrame containing metrics data
        """
        # Check if SQLite DB exists
        if os.path.exists(self.metrics_db):
            return self._load_from_sqlite(start_date, end_date)
        else:
            # Fall back to JSON logs
            return self._load_from_json_logs(start_date, end_date)
    
    def _load_from_sqlite(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Load metrics from SQLite database"""
        try:
            with SqliteDict(self.metrics_db, tablename="path_metrics") as db:
                # Filter metrics by date range
                metrics = []
                for key, value in db.items():
                    timestamp = datetime.fromisoformat(value.get("timestamp", "2000-01-01"))
                    if start_date <= timestamp.date() <= end_date:
                        metrics.append(value)
                
                if metrics:
                    return pd.DataFrame(metrics)
                else:
                    return pd.DataFrame()
        except Exception as e:
            print(f"Error loading metrics from SQLite: {e}")
            return pd.DataFrame()
    
    def _load_from_json_logs(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Load metrics from JSON log files"""
        metrics = []
        
        # Find log files in the specified date range
        log_files = list(Path(self.logs_dir).glob("path_metrics_*.json"))
        
        for log_file in log_files:
            try:
                file_date_str = log_file.stem.replace("path_metrics_", "")
                file_date = datetime.strptime(file_date_str, "%Y%m%d").date()
                
                if start_date <= file_date <= end_date:
                    with open(log_file, 'r') as f:
                        file_metrics = json.load(f)
                        metrics.extend(file_metrics)
            except Exception as e:
                print(f"Error processing log file {log_file}: {e}")
        
        if metrics:
            return pd.DataFrame(metrics)
        else:
            return pd.DataFrame()
    
    def get_recent_queries(self, start_date: datetime, end_date: datetime, limit: int = 100) -> pd.DataFrame:
        """
        Get a list of recent queries
        
        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum number of queries to return
            
        Returns:
            DataFrame with query information
        """
        metrics_df = self.load_metrics(start_date, end_date)
        
        if metrics_df.empty:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=["query_id", "query_text", "timestamp"])
        
        # Sort by timestamp (descending) and take the first 'limit' rows
        recent = metrics_df.sort_values("timestamp", ascending=False).head(limit)
        
        # Select only the columns we need
        query_df = recent[["query_id", "query_text", "timestamp"]].copy()
        
        return query_df
    
    def get_query_details(self, query_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific query
        
        Args:
            query_id: ID of the query to retrieve
            
        Returns:
            Dictionary with query details
        """
        try:
            # Try to load from SQLite first
            if os.path.exists(self.metrics_db):
                with SqliteDict(self.metrics_db, tablename="path_metrics") as db:
                    # Look for the query by ID
                    for key, value in db.items():
                        if value.get("query_id") == query_id:
                            return value
            
            # Fall back to JSON logs
            for log_file in Path(self.logs_dir).glob("path_metrics_*.json"):
                with open(log_file, 'r') as f:
                    metrics = json.load(f)
                    for metric in metrics:
                        if metric.get("query_id") == query_id:
                            return metric
            
            # Query not found
            return {
                "query_id": query_id,
                "query_text": "Query not found",
                "paths_explored": 0,
                "max_depth": 0,
                "pruning_efficiency": 0,
                "final_path": [],
                "paths": []
            }
        except Exception as e:
            print(f"Error getting query details: {e}")
            return {
                "query_id": query_id,
                "query_text": f"Error retrieving query: {str(e)}",
                "paths_explored": 0,
                "max_depth": 0,
                "pruning_efficiency": 0,
                "final_path": [],
                "paths": []
            }

# Create global instance for easy imports
collector = PathRAGMetricsCollector()

# Exported functions that use the collector instance
def load_metrics(start_date, end_date):
    """Load metrics for the date range"""
    return collector.load_metrics(start_date, end_date)

def get_recent_queries(start_date, end_date, limit=100):
    """Get recent queries"""
    return collector.get_recent_queries(start_date, end_date, limit)

def get_query_details(query_id):
    """Get details for a specific query"""
    return collector.get_query_details(query_id)

# Sample data generation for development/testing
def generate_sample_data(output_db: str, num_samples: int = 100):
    """
    Generate sample metrics data for development and testing
    
    Args:
        output_db: Path to output database
        num_samples: Number of sample metrics to generate
    """
    import random
    import uuid
    from datetime import datetime, timedelta
    
    # Sample queries
    sample_queries = [
        "How does the transformer architecture work?",
        "Explain the attention mechanism in deep learning",
        "What are the advantages of PathRAG over traditional RAG?",
        "Describe the implementation of self-attention",
        "How do I implement beam search for language models?",
        "What is the difference between LSTM and GRU?",
        "Explain the concept of knowledge distillation",
        "How do I fine-tune a pre-trained model?",
        "What are the challenges in few-shot learning?",
        "Explain the concept of contrastive learning"
    ]
    
    # Generate sample metrics
    metrics = []
    
    for i in range(num_samples):
        # Random query
        query_text = random.choice(sample_queries)
        query_id = str(uuid.uuid4())
        
        # Random timestamp within the last 30 days
        days_ago = random.randint(0, 30)
        timestamp = (datetime.now() - timedelta(days=days_ago)).isoformat()
        
        # Random path metrics
        paths_explored = random.randint(5, 50)
        max_depth = random.randint(3, 10)
        pruning_efficiency = random.random() * 0.8 + 0.1  # Between 0.1 and 0.9
        
        # Generate random paths
        paths = []
        for j in range(min(paths_explored, 10)):  # Store up to 10 paths for sample data
            path_length = random.randint(1, max_depth)
            path = [f"node_{random.randint(1, 100)}" for _ in range(path_length)]
            paths.append(path)
        
        # Select a final path
        final_path = random.choice(paths) if paths else []
        
        # Create metric record
        metric = {
            "query_id": query_id,
            "query_text": query_text,
            "timestamp": timestamp,
            "paths_explored": paths_explored,
            "max_depth": max_depth,
            "avg_branching": random.random() * 3 + 1,  # Between 1 and 4
            "pruning_efficiency": pruning_efficiency,
            "final_path_length": len(final_path),
            "final_path": final_path,
            "paths": paths
        }
        
        metrics.append(metric)
    
    # Save to SQLite
    with SqliteDict(output_db, tablename="path_metrics", autocommit=True) as db:
        for i, metric in enumerate(metrics):
            db[f"metric_{i}"] = metric
    
    print(f"Generated {num_samples} sample metrics and saved to {output_db}")

if __name__ == "__main__":
    # If run directly, generate sample data
    import argparse
    
    parser = argparse.ArgumentParser(description="PathRAG Metrics Collector")
    parser.add_argument("--generate-samples", action="store_true", help="Generate sample data")
    parser.add_argument("--num-samples", type=int, default=100, help="Number of samples to generate")
    parser.add_argument("--output-db", type=str, default=DEFAULT_METRICS_DB, help="Output database path")
    
    args = parser.parse_args()
    
    if args.generate_samples:
        generate_sample_data(args.output_db, args.num_samples)
    else:
        print("No action specified. Use --generate-samples to create sample data.")
