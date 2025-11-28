#!/usr/bin/env python3
"""
PathRAG Monitor - A visualization tool for PathRAG retrieval paths and metrics

This Streamlit application provides interactive visualizations of PathRAG's graph 
traversal metrics, path selection, and performance statistics.
"""

import streamlit as st
import networkx as nx
import plotly.graph_objects as go
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from pathlib import Path

from metrics_collector import load_metrics, get_recent_queries, get_query_details
from graph_visualizer import build_networkx_graph, create_graph_visualization
from phoenix_connector import check_phoenix_connection, get_phoenix_projects, get_path_metrics, PHOENIX_PROJECT

# Page configuration
st.set_page_config(
    page_title="PathRAG Monitor",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar with filters
st.sidebar.title("PathRAG Monitor")
st.sidebar.info("Visualize and analyze graph traversal paths and metrics for PathRAG retrieval")

# Phoenix connection status
phoenix_connected = check_phoenix_connection()
if phoenix_connected:
    st.sidebar.success("✅ Connected to Phoenix")
    
    # Get Phoenix projects
    projects = get_phoenix_projects()
    if PHOENIX_PROJECT in projects:
        st.sidebar.success(f"✅ PathRAG project '{PHOENIX_PROJECT}' found")
    else:
        st.sidebar.warning(f"⚠️ PathRAG project '{PHOENIX_PROJECT}' not found")
        st.sidebar.info(f"Available projects: {', '.join(projects) if projects else 'None'}")
else:
    st.sidebar.error("❌ Not connected to Phoenix")
    st.sidebar.info("Please ensure Phoenix is running")

# Date range filter
default_start = datetime.now() - timedelta(days=7)
default_end = datetime.now()
start_date = st.sidebar.date_input("Start Date", default_start)
end_date = st.sidebar.date_input("End Date", default_end)

# Path metrics filters
st.sidebar.subheader("Path Filters")
min_path_length = st.sidebar.slider("Min Path Length", 1, 10, 1)
max_path_length = st.sidebar.slider("Max Path Length", 1, 20, 10)
min_pruning_efficiency = st.sidebar.slider("Min Pruning Efficiency (%)", 0, 100, 0)

# Main content area with tabs
tab1, tab2, tab3 = st.tabs(["Path Visualization", "Metrics Dashboard", "Query Analysis"])

with tab1:
    st.header("Path Visualization")
    
    # Phoenix data source option
    use_phoenix = st.checkbox("Use Phoenix data", value=phoenix_connected)
    
    if use_phoenix and phoenix_connected:
        # Load path metrics from Phoenix
        st.info(f"Loading path data from Phoenix project: {PHOENIX_PROJECT}")
        path_metrics = get_path_metrics(PHOENIX_PROJECT, start_date, end_date)
        
        if path_metrics.empty:
            st.warning("No path data found in Phoenix for the selected date range")
        else:
            st.success(f"Found {len(path_metrics)} paths in Phoenix")
            
            # Select a trace to visualize
            trace_ids = path_metrics['trace_id'].unique()
            selected_trace = st.selectbox("Select a trace to visualize", trace_ids)
            
            # Filter metrics for selected trace
            trace_paths = path_metrics[path_metrics['trace_id'] == selected_trace]
            
            if not trace_paths.empty:
                # Display trace info
                st.subheader("Trace Information")
                query = trace_paths['query'].iloc[0] if 'query' in trace_paths.columns else "Unknown query"
                st.write(f"**Query:** {query}")
                st.write(f"**Timestamp:** {trace_paths['timestamp'].iloc[0]}")
                st.write(f"**Paths found:** {len(trace_paths)}")
                
                # Create graph visualization
                st.subheader("Path Graph")
                
                # Extract path nodes from the first path
                try:
                    path_nodes = json.loads(trace_paths['path_nodes'].iloc[0])
                    G = build_networkx_graph(path_nodes)
                    fig = create_graph_visualization(G)
                    st.plotly_chart(fig, use_container_width=True)
                except (json.JSONDecodeError, KeyError, IndexError):
                    st.error("Could not parse path nodes from trace data")
                    
                # Display path metrics table
                st.subheader("Path Metrics")
                display_cols = ['path_id', 'path_length', 'path_score', 'nodes_visited', 'edges_traversed', 'latency_ms']
                display_cols = [col for col in display_cols if col in trace_paths.columns]
                st.dataframe(trace_paths[display_cols])
    else:
        # Query selection
        recent_queries = get_recent_queries(start_date, end_date)
        selected_query_id = st.selectbox(
            "Select Query", 
            options=recent_queries["query_id"].tolist(),
            format_func=lambda x: f"{recent_queries[recent_queries['query_id'] == x]['query_text'].iloc[0][:50]}... ({x})"
        )
        
        if selected_query_id:
            # Load query details and paths
            query_details = get_query_details(selected_query_id)
            
            # Show query metadata
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Paths Explored", query_details["paths_explored"])
            with col2:
                st.metric("Max Depth", query_details["max_depth"])
            with col3:
                st.metric("Pruning Efficiency", f"{query_details['pruning_efficiency']:.2%}")
            
            # Build and display graph
            G = build_networkx_graph(query_details["paths"])
            fig = create_graph_visualization(G, query_details["final_path"])
            st.plotly_chart(fig, use_container_width=True)
            
            # Show path details
            with st.expander("Path Details"):
                st.write(query_details["paths"])

with tab2:
    st.header("Metrics Dashboard")
    
    # Load metrics data
    metrics_df = load_metrics(start_date, end_date)
    
    if not metrics_df.empty:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Queries", len(metrics_df))
        with col2:
            st.metric("Avg Path Length", f"{metrics_df['final_path_length'].mean():.2f}")
        with col3:
            st.metric("Avg Paths Explored", f"{metrics_df['paths_explored'].mean():.2f}")
        with col4:
            st.metric("Avg Pruning Efficiency", f"{metrics_df['pruning_efficiency'].mean():.2%}")
        
        # Time series charts
        st.subheader("Performance Over Time")
        metrics_df['timestamp'] = pd.to_datetime(metrics_df['timestamp'])
        metrics_df = metrics_df.set_index('timestamp').sort_index()
        
        # Resample by day
        daily_metrics = metrics_df.resample('D').mean()
        
        # Plot metrics over time
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(daily_metrics.index, daily_metrics['final_path_length'], label='Avg Path Length')
        ax.plot(daily_metrics.index, daily_metrics['paths_explored'], label='Avg Paths Explored')
        ax.plot(daily_metrics.index, daily_metrics['pruning_efficiency']*10, label='Pruning Efficiency (x10)')
        ax.legend()
        ax.set_xlabel('Date')
        ax.set_ylabel('Value')
        st.pyplot(fig)
        
        # Distribution charts
        st.subheader("Metric Distributions")
        col1, col2 = st.columns(2)
        with col1:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.hist(metrics_df['final_path_length'], bins=20)
            ax.set_xlabel('Path Length')
            ax.set_ylabel('Frequency')
            ax.set_title('Distribution of Path Lengths')
            st.pyplot(fig)
        
        with col2:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.hist(metrics_df['pruning_efficiency'], bins=20)
            ax.set_xlabel('Pruning Efficiency')
            ax.set_ylabel('Frequency')
            ax.set_title('Distribution of Pruning Efficiency')
            st.pyplot(fig)
    else:
        st.warning("No metrics data available for the selected date range.")

with tab3:
    st.header("Query Analysis")
    
    # Load metrics data if not already loaded
    if 'metrics_df' not in locals() or metrics_df.empty:
        metrics_df = load_metrics(start_date, end_date)
    
    if not metrics_df.empty:
        # Query categorization
        st.subheader("Query Performance by Type")
        
        # Get query metrics by category (assuming categories exist in the data)
        if 'query_category' in metrics_df.columns:
            category_metrics = metrics_df.groupby('query_category').mean()
            
            fig, ax = plt.subplots(figsize=(10, 6))
            bar_width = 0.35
            index = range(len(category_metrics.index))
            
            ax.bar([i - bar_width/2 for i in index], category_metrics['final_path_length'], 
                   width=bar_width, label='Avg Path Length')
            ax.bar([i + bar_width/2 for i in index], category_metrics['paths_explored'], 
                   width=bar_width, label='Avg Paths Explored')
            
            ax.set_xticks(index)
            ax.set_xticklabels(category_metrics.index)
            ax.legend()
            st.pyplot(fig)
        else:
            st.info("Query categorization not available in the metrics data.")
        
        # Top performing and problematic queries
        st.subheader("Query Performance Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("Top 5 Most Efficient Queries")
            top_efficient = metrics_df.nlargest(5, 'pruning_efficiency')
            st.dataframe(top_efficient[['query_text', 'pruning_efficiency', 'paths_explored', 'final_path_length']])
        
        with col2:
            st.write("Top 5 Least Efficient Queries")
            least_efficient = metrics_df.nsmallest(5, 'pruning_efficiency')
            st.dataframe(least_efficient[['query_text', 'pruning_efficiency', 'paths_explored', 'final_path_length']])
    else:
        st.warning("No query data available for the selected date range.")

if __name__ == "__main__":
    # This will run when the script is executed directly
    pass
