from __future__ import annotations

from collections import defaultdict

import networkx as nx


def compute_layout(nodes: list, edges: list) -> dict:
    """
    Compute a layered left-to-right DAG layout.
    Returns {node_id: (x, y)} in scene coordinates.
    Graph grows rightwards (x increases with generation).
    """
    if not nodes:
        return {}

    H_SPACING = 280
    V_SPACING = 150

    g = nx.DiGraph()
    for n in nodes:
        g.add_node(n.id)
    for e in edges:
        g.add_edge(e.source_id, e.target_id)

    # Compute generation (layer) — longest path from any source
    generation = {}
    sources = [n for n in g.nodes if g.in_degree(n) == 0]

    if sources:
        for src in sources:
            _assign_layers(g, src, generation)

    # Ensure all nodes have a generation
    for n in nodes:
        if n.id not in generation:
            generation[n.id] = 0

    # Group nodes by generation
    layers = defaultdict(list)
    for n in nodes:
        layers[generation[n.id]].append(n.id)

    max_gen = max(layers.keys()) if layers else 0

    # Sort nodes within each layer for stable layout
    ordered_layers = {}
    for gen in range(max_gen + 1):
        layer_nodes = layers.get(gen, [])
        if gen == 0:
            # For gen 0, sort by creation time so isolated root nodes
            # spread out horizontally rather than stacking vertically
            layer_nodes = _sort_gen0_nodes(layer_nodes, nodes, generation, edges)
        else:
            layer_nodes = _barycenter_order(g, layer_nodes, ordered_layers.get(gen - 1, []))
        ordered_layers[gen] = layer_nodes

    # Give isolated gen-0 nodes (no successors) their own columns
    # so the graph clearly grows rightwards
    isolated_gen0 = []
    connected_gen0 = []
    for nid in ordered_layers.get(0, []):
        if g.out_degree(nid) == 0 and g.in_degree(nid) == 0:
            isolated_gen0.append(nid)
        else:
            connected_gen0.append(nid)

    # Assign positions
    positions = {}

    # Connected nodes by generation (left-to-right)
    for gen in range(max_gen + 1):
        layer = ordered_layers.get(gen, [])
        if gen == 0:
            layer = connected_gen0
        y_start = -(len(layer) - 1) * V_SPACING / 2
        for i, node_id in enumerate(layer):
            positions[node_id] = (gen * H_SPACING, y_start + i * V_SPACING)

    # Isolated nodes stack vertically below connected nodes
    if isolated_gen0:
        # Find the bottom of all connected nodes
        max_y = 0
        for (_x, y) in positions.values():
            if y > max_y:
                max_y = y
        iso_y_start = max_y + V_SPACING * 1.5
        for i, nid in enumerate(isolated_gen0):
            positions[nid] = (0, iso_y_start + i * V_SPACING)

    return positions


def _sort_gen0_nodes(node_ids: list[str], nodes: list, generation: dict, edges: list) -> list[str]:
    """Sort gen 0 nodes: those with children first, then by creation time."""
    node_map = {n.id: n for n in nodes}

    # Build successor count
    edge_targets = set()
    for e in edges:
        edge_targets.add(e.target_id)

    has_children = []
    no_children = []
    for nid in node_ids:
        # Mark nodes that have successors
        is_source = any(e.source_id == nid for e in edges)
        if is_source:
            has_children.append(nid)
        else:
            no_children.append(nid)

    # Sort by creation time
    no_children.sort(key=lambda nid: node_map.get(nid, None).created_at if node_map.get(nid) else 0)
    has_children.sort(key=lambda nid: node_map.get(nid, None).created_at if node_map.get(nid) else 0)

    return has_children + no_children


def _assign_layers(g: nx.DiGraph, node: str, generation: dict) -> None:
    """Assign layers via DFS, ensuring longest-path semantics."""
    current = generation.get(node, 0)
    for succ in g.successors(node):
        candidate = current + 1
        if generation.get(succ, -1) < candidate:
            generation[succ] = candidate
            _assign_layers(g, succ, generation)


def _barycenter_order(g: nx.DiGraph, layer: list[str], prev_layer: list[str]) -> list[str]:
    """Order nodes by the average position of their predecessors."""
    if not prev_layer:
        return layer

    prev_rank = {nid: i for i, nid in enumerate(prev_layer)}

    def barycenter(nid):
        preds = list(g.predecessors(nid))
        if not preds:
            return float("inf")
        ranks = [prev_rank.get(p, 0) for p in preds]
        return sum(ranks) / len(ranks)

    return sorted(layer, key=barycenter)


def get_descendants(node_id: str, nodes: list, edges: list) -> set[str]:
    """Return all descendant node IDs."""
    g = nx.DiGraph()
    for n in nodes:
        g.add_node(n.id)
    for e in edges:
        g.add_edge(e.source_id, e.target_id)
    if node_id not in g:
        return set()
    return {d for d in nx.descendants(g, node_id)}
