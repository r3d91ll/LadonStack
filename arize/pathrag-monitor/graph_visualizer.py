#!/usr/bin/env python3
"""
PathRAG Monitor - Graph Visualizer

This module handles the visualization of PathRAG knowledge graphs and traversal paths
using NetworkX and Plotly for interactive exploration.
"""

import networkx as nx
import plotly.graph_objects as go
import numpy as np
from typing import Dict, List, Tuple, Any, Optional

def build_networkx_graph(paths: List[List[str]]) -> nx.DiGraph:
    """
    Build a NetworkX directed graph from a list of paths
    
    Args:
        paths: List of paths, where each path is a list of node IDs
        
    Returns:
        NetworkX DiGraph representation of the paths
    """
    G = nx.DiGraph()
    
    # Add all nodes and edges from all paths
    for path in paths:
        for i in range(len(path)):
            # Add the current node
            if not G.has_node(path[i]):
                G.add_node(path[i])
            
            # Add edge to next node if it exists
            if i < len(path) - 1:
                G.add_edge(path[i], path[i+1])
    
    return G

def create_graph_visualization(G: nx.DiGraph, 
                              highlight_path: Optional[List[str]] = None,
                              layout_algo: str = "spring") -> go.Figure:
    """
    Create an interactive Plotly visualization of the graph
    
    Args:
        G: NetworkX graph to visualize
        highlight_path: Optional path to highlight in the visualization
        layout_algo: Layout algorithm to use ('spring', 'circular', 'kamada_kawai', etc.)
        
    Returns:
        Plotly figure with interactive graph visualization
    """
    # Choose layout algorithm
    if layout_algo == "spring":
        pos = nx.spring_layout(G, seed=42)
    elif layout_algo == "circular":
        pos = nx.circular_layout(G)
    elif layout_algo == "kamada_kawai":
        pos = nx.kamada_kawai_layout(G)
    else:
        pos = nx.spring_layout(G, seed=42)
    
    # Create edge traces
    edge_x = []
    edge_y = []
    highlight_edge_x = []
    highlight_edge_y = []
    
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        
        # Check if this edge is part of the highlighted path
        if (highlight_path and 
            edge[0] in highlight_path and 
            edge[1] in highlight_path and
            highlight_path.index(edge[1]) == highlight_path.index(edge[0]) + 1):
            # This is a highlighted edge
            highlight_edge_x.extend([x0, x1, None])
            highlight_edge_y.extend([y0, y1, None])
        else:
            # Regular edge
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
    
    # Create regular edge trace
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines'
    )
    
    # Create highlighted edge trace if needed
    if highlight_path and highlight_edge_x:
        highlight_edge_trace = go.Scatter(
            x=highlight_edge_x, y=highlight_edge_y,
            line=dict(width=3, color='red'),
            hoverinfo='none',
            mode='lines'
        )
    else:
        highlight_edge_trace = None
    
    # Create regular node trace
    node_x = []
    node_y = []
    node_text = []
    node_sizes = []
    node_colors = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(str(node))
        
        # Different size/color if it's in the highlighted path
        if highlight_path and node in highlight_path:
            node_sizes.append(15)
            node_colors.append('red')
        else:
            node_sizes.append(10)
            node_colors.append('#1f77b4')  # Default blue
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            showscale=False,
            color=node_colors,
            size=node_sizes,
            line=dict(width=1, color='#888')
        )
    )
    
    # Create figure
    fig = go.Figure(
        data=[edge_trace, node_trace] + ([highlight_edge_trace] if highlight_edge_trace else []),
        layout=go.Layout(
            title='PathRAG Knowledge Graph Traversal',
            titlefont=dict(size=16),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
    )
    
    return fig

def create_subgraph_visualization(G: nx.DiGraph, 
                                 center_node: str,
                                 depth: int = 2) -> go.Figure:
    """
    Create a visualization focusing on a subgraph around a center node
    
    Args:
        G: Full graph
        center_node: Node to center the visualization on
        depth: How many hops away from center to include
        
    Returns:
        Plotly figure with the subgraph visualization
    """
    # Create subgraph with nodes within 'depth' distance of center_node
    subgraph_nodes = {center_node}
    frontier = {center_node}
    
    for _ in range(depth):
        new_frontier = set()
        for node in frontier:
            # Add neighbors (both incoming and outgoing)
            new_frontier.update(G.neighbors(node))
            new_frontier.update(G.predecessors(node))
        frontier = new_frontier - subgraph_nodes
        subgraph_nodes.update(frontier)
    
    # Create subgraph
    subgraph = G.subgraph(subgraph_nodes)
    
    # Create layout with center node in the middle
    pos = nx.spring_layout(subgraph, seed=42)
    
    # Adjust center node position to be in the middle
    center_x = sum(x for x, y in pos.values()) / len(pos)
    center_y = sum(y for x, y in pos.values()) / len(pos)
    
    # Move center node to middle and adjust other positions
    pos[center_node] = (0, 0)
    for node in subgraph.nodes():
        if node != center_node:
            x, y = pos[node]
            pos[node] = (x - center_x, y - center_y)
    
    # Create edge traces
    edge_x = []
    edge_y = []
    edge_colors = []
    
    for u, v in subgraph.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        
        # Color edges based on distance from center
        if u == center_node or v == center_node:
            edge_colors.extend(['red', 'red', 'red'])
        else:
            edge_colors.extend(['#888', '#888', '#888'])
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color=edge_colors),
        hoverinfo='none',
        mode='lines'
    )
    
    # Create node trace with different colors/sizes based on distance from center
    node_x = []
    node_y = []
    node_text = []
    node_colors = []
    node_sizes = []
    
    for node in subgraph.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(str(node))
        
        if node == center_node:
            node_colors.append('red')
            node_sizes.append(20)
        else:
            # Calculate shortest path distance to color by proximity
            try:
                distance = nx.shortest_path_length(subgraph, center_node, node)
            except (nx.NetworkXNoPath, nx.NetworkXError):
                try:
                    distance = nx.shortest_path_length(subgraph, node, center_node)
                except (nx.NetworkXNoPath, nx.NetworkXError):
                    distance = depth  # Max distance if no path exists
            
            # Color gradient based on distance
            color_intensity = max(0, 1 - (distance / depth))
            node_colors.append(f'rgba(31, 119, 180, {color_intensity:.2f})')
            node_sizes.append(15 - (distance * 2))
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            showscale=False,
            color=node_colors,
            size=node_sizes,
            line=dict(width=1, color='#888')
        )
    )
    
    # Create figure
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title=f'Neighborhood of Node: {center_node}',
            titlefont=dict(size=16),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
    )
    
    return fig


# Utility functions for graph analysis
def find_important_nodes(G: nx.DiGraph, metric: str = 'betweenness') -> Dict[str, float]:
    """
    Identify important nodes in the graph based on various centrality metrics
    
    Args:
        G: NetworkX graph
        metric: Centrality metric to use ('betweenness', 'degree', 'eigenvector', etc.)
        
    Returns:
        Dictionary mapping node IDs to importance scores
    """
    if metric == 'betweenness':
        return nx.betweenness_centrality(G)
    elif metric == 'degree':
        return dict(G.degree())
    elif metric == 'eigenvector':
        return nx.eigenvector_centrality(G, max_iter=1000)
    elif metric == 'pagerank':
        return nx.pagerank(G)
    else:
        return nx.degree_centrality(G)

def analyze_path_efficiency(G: nx.DiGraph, path: List[str]) -> Dict[str, Any]:
    """
    Analyze the efficiency of a path through the graph
    
    Args:
        G: NetworkX graph
        path: Path as a list of node IDs
        
    Returns:
        Dictionary with path efficiency metrics
    """
    if not path or len(path) < 2:
        return {
            "path_length": 0,
            "shortest_path_length": 0,
            "efficiency_ratio": 1.0,
            "unnecessary_nodes": []
        }
    
    # Get start and end nodes
    start_node = path[0]
    end_node = path[-1]
    
    # Calculate shortest path
    try:
        shortest_path = nx.shortest_path(G, start_node, end_node)
        shortest_path_length = len(shortest_path) - 1  # Number of edges
    except (nx.NetworkXNoPath, nx.NetworkXError):
        shortest_path = path
        shortest_path_length = len(path) - 1
    
    # Calculate efficiency
    path_length = len(path) - 1  # Number of edges
    efficiency_ratio = shortest_path_length / path_length if path_length > 0 else 1.0
    
    # Find unnecessary nodes (nodes in the path but not in the shortest path)
    unnecessary_nodes = [node for node in path if node not in shortest_path]
    
    return {
        "path_length": path_length,
        "shortest_path_length": shortest_path_length,
        "efficiency_ratio": efficiency_ratio,
        "unnecessary_nodes": unnecessary_nodes
    }

if __name__ == "__main__":
    # Test with a simple graph if run directly
    G = nx.DiGraph()
    
    # Add some nodes and edges
    for i in range(10):
        G.add_node(f"node_{i}")
    
    for i in range(9):
        G.add_edge(f"node_{i}", f"node_{i+1}")
    
    # Add some cross-connections
    G.add_edge("node_1", "node_5")
    G.add_edge("node_3", "node_7")
    G.add_edge("node_2", "node_8")
    
    # Test visualization
    fig = create_graph_visualization(G, highlight_path=["node_0", "node_1", "node_5", "node_6"])
    
    # Save to HTML file for testing
    import plotly.io as pio
    pio.write_html(fig, "test_graph.html")
    print("Test graph visualization saved to test_graph.html")
