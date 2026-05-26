import networkx as nx
import random
from typing import Any

def calculate_network_influence(edges: list[dict[str, Any]], target_customer_id: str) -> float:
    """
    Computes the PageRank of the target customer based on transaction network edges.
    edges: list of {"source": str, "target": str, "weight": float}
    """
    if not edges:
        return 0.0
        
    G = nx.DiGraph()
    for edge in edges:
        G.add_edge(edge["source"], edge["target"], weight=edge.get("weight", 1.0))
        
    try:
        pagerank_scores = nx.pagerank(G, weight='weight')
    except nx.PowerIterationFailedConvergence:
        return 0.0
    
    # Return the influence score multiplied by a scaling factor for easier interpretation
    return pagerank_scores.get(target_customer_id, 0.0) * 100.0

def get_customer_influence_score(target_customer_id: str, mock_edges: bool = True) -> dict[str, Any]:
    """
    Retrieves or calculates the customer's network influence score.
    """
    edges = []
    if mock_edges:
        edges = _simulate_customer_network(target_customer_id)
        
    score = calculate_network_influence(edges, target_customer_id)
    
    is_hub = score > 2.0  # Threshold for "hub" customer
    
    return {
        "influence_score": round(score, 4),
        "is_hub_customer": is_hub,
        "network_size": len(edges)
    }

def _simulate_customer_network(target_customer_id: str, num_edges: int = 50) -> list[dict[str, Any]]:
    """
    For MVP, generate synthetic network edges around the target customer
    to demonstrate the PageRank calculation.
    """
    edges = []
    random.seed(hash(target_customer_id) % (2**32))
    
    # Target customer receives money
    for i in range(num_edges // 2):
        edges.append({
            "source": f"synthetic_node_{random.randint(1, 100)}",
            "target": target_customer_id,
            "weight": random.uniform(10.0, 5000.0)
        })
    # Target customer sends money
    for i in range(num_edges // 4):
        edges.append({
            "source": target_customer_id,
            "target": f"synthetic_node_{random.randint(101, 200)}",
            "weight": random.uniform(10.0, 1000.0)
        })
    # Random other edges
    for i in range(num_edges // 4):
        edges.append({
            "source": f"synthetic_node_{random.randint(1, 100)}",
            "target": f"synthetic_node_{random.randint(101, 200)}",
            "weight": random.uniform(10.0, 500.0)
        })
    return edges
