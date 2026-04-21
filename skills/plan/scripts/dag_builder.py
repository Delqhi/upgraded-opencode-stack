#!/usr/bin/env python3
"""
Dependency DAG Builder v2.0
Builds a Directed Acyclic Graph from plan tasks and identifies:
- Critical path (longest path through the DAG)
- Parallel execution waves
- Blockers and single points of failure
- Topological sort for execution order

Usage:
    python3 dag_builder.py <plan.json> [--output <graph.json>] [--visualize] [--verbose]

Output:
    Prints execution waves, critical path, and dependency analysis.
    Optionally outputs a JSON graph file and Mermaid diagram.
"""

import json
import sys
import os
from collections import defaultdict, deque
from typing import Any


def parse_duration(duration_str: str) -> float:
    """Parse duration string to hours (e.g., '4h' -> 4.0, '2d' -> 16.0)."""
    if not duration_str:
        return 0.0
    duration_str = duration_str.strip().lower()
    if duration_str.endswith("h"):
        return float(duration_str[:-1])
    elif duration_str.endswith("d"):
        return float(duration_str[:-1]) * 8
    elif duration_str.endswith("w"):
        return float(duration_str[:-1]) * 40
    else:
        try:
            return float(duration_str)
        except ValueError:
            return 0.0


def build_dependency_graph(plan: dict) -> dict:
    """Build a dependency graph from a plan."""
    tasks = {}
    edges = []

    # Extract all tasks from phases
    for phase in plan.get("phases", []):
        phase_id = phase.get("id", "")
        for task in phase.get("tasks", []):
            task_id = task.get("id", "")
            if task_id:
                effort = task.get("effort", {})
                realistic = parse_duration(effort.get("realistic", "0h"))
                tasks[task_id] = {
                    "id": task_id,
                    "description": task.get("description", ""),
                    "phase": phase_id,
                    "phase_name": phase.get("name", ""),
                    "priority": phase.get("priority", "medium"),
                    "duration_hours": realistic,
                    "dependencies": task.get("dependencies", []),
                    "validation": task.get("validation", ""),
                    "status": task.get("status", "not-started"),
                }

    # Build edges from dependencies
    for task_id, task_info in tasks.items():
        for dep in task_info["dependencies"]:
            if dep in tasks:
                edges.append({"from": dep, "to": task_id, "type": "hard"})

    return {"nodes": list(tasks.keys()), "edges": edges, "tasks": tasks}


def detect_cycles(graph: dict) -> list[list[str]]:
    """Detect cycles in the dependency graph using DFS."""
    nodes = graph["nodes"]
    adj = defaultdict(list)
    for edge in graph["edges"]:
        adj[edge["from"]].append(edge["to"])

    cycles = []
    visited = set()
    rec_stack = set()
    path = []

    def dfs(node):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in adj[node]:
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in rec_stack:
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])

        path.pop()
        rec_stack.discard(node)

    for node in nodes:
        if node not in visited:
            dfs(node)

    return cycles


def topological_sort(graph: dict) -> list[str]:
    """Topological sort using Kahn's algorithm."""
    nodes = graph["nodes"]
    in_degree = defaultdict(int)
    adj = defaultdict(list)

    for edge in graph["edges"]:
        adj[edge["from"]].append(edge["to"])
        in_degree[edge["to"]] += 1

    queue = deque([n for n in nodes if in_degree[n] == 0])
    result = []

    while queue:
        node = queue.popleft()
        result.append(node)
        for neighbor in adj[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return result


def find_critical_path(graph: dict) -> dict:
    """Find the critical path (longest path) through the DAG."""
    nodes = graph["nodes"]
    tasks = graph["tasks"]
    adj = defaultdict(list)
    in_degree = defaultdict(int)

    for edge in graph["edges"]:
        adj[edge["from"]].append(edge["to"])
        in_degree[edge["to"]] += 1

    dist = {node: tasks[node]["duration_hours"] for node in nodes}
    parent = {node: None for node in nodes}

    topo_order = topological_sort(graph)

    for node in topo_order:
        for neighbor in adj[node]:
            new_dist = dist[node] + tasks[neighbor]["duration_hours"]
            if new_dist > dist[neighbor]:
                dist[neighbor] = new_dist
                parent[neighbor] = node

    end_node = max(nodes, key=lambda n: dist[n])

    path = []
    current = end_node
    while current is not None:
        path.append(current)
        current = parent[current]
    path.reverse()

    return {
        "path": path,
        "total_hours": dist[end_node],
        "tasks": [tasks[n] for n in path],
    }


def find_execution_waves(graph: dict) -> list[list[str]]:
    """Find parallel execution waves (tasks that can run simultaneously)."""
    nodes = graph["nodes"]
    adj = defaultdict(list)
    in_degree = defaultdict(int)

    for edge in graph["edges"]:
        adj[edge["from"]].append(edge["to"])
        in_degree[edge["to"]] += 1

    waves = []
    remaining = set(nodes)

    while remaining:
        wave = [n for n in remaining if in_degree[n] == 0]
        if not wave:
            break

        waves.append(sorted(wave))

        for node in wave:
            remaining.remove(node)
            for neighbor in adj[node]:
                in_degree[neighbor] -= 1

    return waves


def find_blockers(graph: dict) -> list[dict]:
    """Find tasks that block multiple downstream tasks."""
    adj = defaultdict(list)
    for edge in graph["edges"]:
        adj[edge["from"]].append(edge["to"])

    blockers = []
    for node, dependents in adj.items():
        if len(dependents) >= 2:
            blockers.append(
                {"task": node, "blocks": dependents, "block_count": len(dependents)}
            )

    return sorted(blockers, key=lambda b: b["block_count"], reverse=True)


def find_single_points_of_failure(graph: dict) -> list[dict]:
    """Find tasks that are single points of failure."""
    nodes = graph["nodes"]
    tasks = graph["tasks"]

    spofs = []
    for node in nodes:
        task = tasks[node]
        if task["priority"] == "critical":
            downstream = set()
            queue = deque([node])
            visited = {node}

            while queue:
                current = queue.popleft()
                for edge in graph["edges"]:
                    if edge["from"] == current and edge["to"] not in visited:
                        visited.add(edge["to"])
                        downstream.add(edge["to"])
                        queue.append(edge["to"])

            if downstream:
                spofs.append(
                    {
                        "task": node,
                        "description": task["description"],
                        "downstream_count": len(downstream),
                        "downstream": list(downstream),
                    }
                )

    return sorted(spofs, key=lambda s: s["downstream_count"], reverse=True)


def generate_mermaid(graph: dict, critical_path: dict) -> str:
    """Generate a Mermaid diagram of the dependency graph."""
    lines = ["graph TD"]

    critical_nodes = set(critical_path["path"])

    for task_id, task_info in graph["tasks"].items():
        phase_label = task_info.get("phase_name", "")
        duration = task_info.get("duration_hours", 0)
        label = f"{task_id}<br/>{phase_label}<br/>{duration}h"

        if task_id in critical_nodes:
            lines.append(f'  {task_id.replace("-", "_")}["{label}"]:::critical')
        else:
            lines.append(f'  {task_id.replace("-", "_")}["{label}"]')

    lines.append("")

    for edge in graph["edges"]:
        from_node = edge["from"].replace("-", "_")
        to_node = edge["to"].replace("-", "_")
        if edge.get("type") == "external":
            lines.append(f"  {from_node} -.-> {to_node}")
        else:
            lines.append(f"  {from_node} --> {to_node}")

    lines.append("")
    lines.append("  classDef critical fill:#ff6b6b,stroke:#c92a2a,color:#fff")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python3 dag_builder.py <plan.json> [--output <graph.json>] [--visualize] [--verbose]"
        )
        sys.exit(1)

    plan_file = sys.argv[1]
    output_file = None
    visualize = False
    verbose = False

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--output" and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--visualize":
            visualize = True
            i += 1
        elif sys.argv[i] == "--verbose":
            verbose = True
            i += 1
        else:
            i += 1

    try:
        with open(plan_file) as f:
            plan = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    graph = build_dependency_graph(plan)

    cycles = detect_cycles(graph)
    if cycles:
        print("❌ CYCLES DETECTED (not a valid DAG):")
        for cycle in cycles:
            print(f"  {' -> '.join(cycle)}")
        sys.exit(1)

    topo_order = topological_sort(graph)
    critical_path = find_critical_path(graph)
    waves = find_execution_waves(graph)
    blockers = find_blockers(graph)
    spofs = find_single_points_of_failure(graph)

    print(f"\n{'=' * 60}")
    print(f"  Dependency DAG Analysis: {plan.get('title', 'Unknown')}")
    print(f"{'=' * 60}")
    print(f"  Tasks: {len(graph['nodes'])}")
    print(f"  Dependencies: {len(graph['edges'])}")
    print(f"  Critical Path Duration: {critical_path['total_hours']:.1f}h")
    print(f"  Execution Waves: {len(waves)}")
    print(f"{'=' * 60}")

    print(f"\n  CRITICAL PATH:")
    for task_id in critical_path["path"]:
        task = graph["tasks"][task_id]
        print(f"    → {task_id} ({task['duration_hours']:.1f}h) [{task['phase_name']}]")

    print(f"\n  EXECUTION WAVES:")
    for i, wave in enumerate(waves):
        total_hours = sum(graph["tasks"][t]["duration_hours"] for t in wave)
        print(
            f"    Wave {i + 1}: {', '.join(wave)} (parallel: {total_hours:.1f}h total)"
        )

    if blockers:
        print(f"\n  BLOCKERS (tasks blocking 2+ others):")
        for blocker in blockers:
            print(
                f"    ⚠️  {blocker['task']} blocks {blocker['block_count']} tasks: {', '.join(blocker['blocks'])}"
            )

    if spofs:
        print(f"\n  SINGLE POINTS OF FAILURE:")
        for spof in spofs:
            print(f"    🔴 {spof['task']}: {spof['description']}")
            print(f"       Affects {spof['downstream_count']} downstream tasks")

    if visualize:
        mermaid = generate_mermaid(graph, critical_path)
        print(f"\n  MERMAID DIAGRAM:")
        print(f"  ```mermaid")
        print(mermaid)
        print(f"  ```")

    if output_file:
        output = {
            "nodes": graph["nodes"],
            "edges": graph["edges"],
            "critical_path": critical_path["path"],
            "critical_path_hours": critical_path["total_hours"],
            "execution_waves": waves,
            "blockers": blockers,
            "single_points_of_failure": spofs,
            "tasks": graph["tasks"],
        }
        with open(output_file, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\n  Graph saved to: {output_file}")

    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    main()
