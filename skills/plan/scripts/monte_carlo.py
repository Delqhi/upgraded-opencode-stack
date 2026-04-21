#!/usr/bin/env python3
"""
Monte Carlo Estimation v2.0
Performs Monte Carlo simulation on plan tasks with 3-point estimates.
Outputs confidence intervals, probability distributions, and risk assessment.

Uses PERT distribution:
  Expected = (Pessimistic + 4*Realistic + Optimistic) / 6
  StdDev = (Pessimistic - Optimistic) / 6

Runs 10,000 simulations to estimate project duration with confidence intervals.

Usage:
    python3 monte_carlo.py <plan.json> [--iterations 10000] [--output results.json] [--verbose] [--chart]

Output:
    Prints confidence intervals, probability of on-time delivery, and risk assessment.
"""

import json
import sys
import os
import random
import math
from typing import Any


def parse_duration(duration_str: str) -> float:
    """Parse duration string to hours."""
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


def extract_task_estimates(plan: dict) -> list[dict]:
    """Extract 3-point estimates from all tasks in the plan."""
    tasks = []
    for phase in plan.get("phases", []):
        for task in phase.get("tasks", []):
            effort = task.get("effort", {})
            if all(k in effort for k in ["pessimistic", "realistic", "optimistic"]):
                pessimistic = parse_duration(effort["pessimistic"])
                realistic = parse_duration(effort["realistic"])
                optimistic = parse_duration(effort["optimistic"])

                tasks.append(
                    {
                        "id": task.get("id", ""),
                        "description": task.get("description", ""),
                        "phase": phase.get("id", ""),
                        "pessimistic": pessimistic,
                        "realistic": realistic,
                        "optimistic": optimistic,
                        "expected": (pessimistic + 4 * realistic + optimistic) / 6,
                        "std_dev": (pessimistic - optimistic) / 6,
                    }
                )

    return tasks


def pert_random(expected: float, std_dev: float) -> float:
    """Generate a random duration using PERT distribution approximation."""
    min_val = expected - 3 * std_dev
    max_val = expected + 3 * std_dev
    return max(min_val, min(max_val, random.gauss(expected, std_dev)))


def run_monte_carlo(tasks: list[dict], iterations: int = 10000) -> dict:
    """Run Monte Carlo simulation with the given tasks."""
    if not tasks:
        return {"error": "No tasks with 3-point estimates found"}

    sim_results = []

    for _ in range(iterations):
        total_duration = 0
        for task in tasks:
            duration = pert_random(task["expected"], task["std_dev"])
            total_duration += max(0, duration)
        sim_results.append(total_duration)

    sim_results.sort()

    percentiles = {
        "p10": sim_results[int(0.10 * iterations)],
        "p25": sim_results[int(0.25 * iterations)],
        "p50": sim_results[int(0.50 * iterations)],
        "p75": sim_results[int(0.75 * iterations)],
        "p85": sim_results[int(0.85 * iterations)],
        "p90": sim_results[int(0.90 * iterations)],
        "p95": sim_results[int(0.95 * iterations)],
        "p99": sim_results[int(0.99 * iterations)],
    }

    mean_duration = sum(sim_results) / iterations
    variance = sum((x - mean_duration) ** 2 for x in sim_results) / iterations
    std_dev = math.sqrt(variance)

    min_duration = sim_results[0]
    max_duration = sim_results[-1]

    expected_total = sum(t["expected"] for t in tasks)
    pessimistic_total = sum(t["pessimistic"] for t in tasks)
    optimistic_total = sum(t["optimistic"] for t in tasks)

    return {
        "iterations": iterations,
        "task_count": len(tasks),
        "summary": {
            "mean": mean_duration,
            "std_dev": std_dev,
            "min": min_duration,
            "max": max_duration,
            "expected_total": expected_total,
            "pessimistic_total": pessimistic_total,
            "optimistic_total": optimistic_total,
        },
        "percentiles": percentiles,
        "confidence_intervals": {
            "50%": f"{percentiles['p50']:.1f}h",
            "85%": f"{percentiles['p85']:.1f}h",
            "95%": f"{percentiles['p95']:.1f}h",
        },
    }


def calculate_on_time_probability(results: dict, target_hours: float) -> float:
    """Calculate probability of completing within target hours."""
    sim_results = results.get("_raw_results", [])
    if not sim_results:
        return 0.0
    on_time = sum(1 for r in sim_results if r <= target_hours)
    return (on_time / len(sim_results)) * 100


def identify_high_risk_tasks(tasks: list[dict]) -> list[dict]:
    """Identify tasks with high uncertainty (large spread between estimates)."""
    high_risk = []
    for task in tasks:
        if task["pessimistic"] > 0:
            uncertainty_ratio = (task["pessimistic"] - task["optimistic"]) / task[
                "pessimistic"
            ]
            if uncertainty_ratio > 0.5:
                high_risk.append(
                    {
                        "id": task["id"],
                        "description": task["description"],
                        "uncertainty_ratio": uncertainty_ratio,
                        "pessimistic": task["pessimistic"],
                        "optimistic": task["optimistic"],
                        "expected": task["expected"],
                    }
                )

    return sorted(high_risk, key=lambda t: t["uncertainty_ratio"], reverse=True)


def generate_histogram_data(results: dict, bins: int = 20) -> list[dict]:
    """Generate histogram data for visualization."""
    sim_results = results.get("_raw_results", [])
    if not sim_results:
        return []

    min_val = min(sim_results)
    max_val = max(sim_results)
    bin_width = (max_val - min_val) / bins

    histogram = []
    for i in range(bins):
        bin_start = min_val + i * bin_width
        bin_end = bin_start + bin_width
        count = sum(1 for r in sim_results if bin_start <= r < bin_end)
        histogram.append(
            {
                "range": f"{bin_start:.1f}-{bin_end:.1f}h",
                "count": count,
                "probability": count / len(sim_results) * 100,
            }
        )

    return histogram


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python3 monte_carlo.py <plan.json> [--iterations 10000] [--output results.json] [--verbose] [--chart]"
        )
        sys.exit(1)

    plan_file = sys.argv[1]
    iterations = 10000
    output_file = None
    verbose = False
    chart = False

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--iterations" and i + 1 < len(sys.argv):
            iterations = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--output" and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--verbose":
            verbose = True
            i += 1
        elif sys.argv[i] == "--chart":
            chart = True
            i += 1
        else:
            i += 1

    try:
        with open(plan_file) as f:
            plan = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    tasks = extract_task_estimates(plan)
    if not tasks:
        print("ERROR: No tasks with 3-point estimates found in plan")
        sys.exit(1)

    random.seed(42)

    sim_results_list = []
    for _ in range(iterations):
        total = sum(pert_random(t["expected"], t["std_dev"]) for t in tasks)
        sim_results_list.append(max(0, total))

    results = run_monte_carlo(tasks, iterations)
    results["_raw_results"] = sim_results_list

    high_risk = identify_high_risk_tasks(tasks)

    print(f"\n{'=' * 60}")
    print(f"  Monte Carlo Estimation: {plan.get('title', 'Unknown')}")
    print(f"{'=' * 60}")
    print(f"  Tasks with estimates: {len(tasks)}")
    print(f"  Simulations: {iterations:,}")
    print(f"{'=' * 60}")

    print(f"\n  CLASSICAL PERT ESTIMATES:")
    print(f"    Optimistic:   {results['summary']['optimistic_total']:.1f}h")
    print(f"    Expected:     {results['summary']['expected_total']:.1f}h")
    print(f"    Pessimistic:  {results['summary']['pessimistic_total']:.1f}h")

    print(f"\n  MONTE CARLO RESULTS:")
    print(f"    Mean:         {results['summary']['mean']:.1f}h")
    print(f"    Std Dev:      {results['summary']['std_dev']:.1f}h")
    print(f"    Min:          {results['summary']['min']:.1f}h")
    print(f"    Max:          {results['summary']['max']:.1f}h")

    print(f"\n  CONFIDENCE INTERVALS:")
    print(f"    50% (median): {results['percentiles']['p50']:.1f}h")
    print(f"    85%:          {results['percentiles']['p85']:.1f}h")
    print(f"    95%:          {results['percentiles']['p95']:.1f}h")

    print(f"\n  RISK ASSESSMENT:")
    risk_score = results["summary"]["std_dev"] / results["summary"]["mean"] * 100
    if risk_score < 15:
        risk_label = "LOW - Estimates are reliable"
        risk_emoji = "🟢"
    elif risk_score < 30:
        risk_label = "MEDIUM - Some uncertainty"
        risk_emoji = "🟡"
    elif risk_score < 50:
        risk_label = "HIGH - Significant uncertainty"
        risk_emoji = "🟠"
    else:
        risk_label = "CRITICAL - Estimates unreliable"
        risk_emoji = "🔴"

    print(f"    {risk_emoji} Risk Score: {risk_score:.1f}% ({risk_label})")

    if high_risk:
        print(f"\n  HIGH UNCERTAINTY TASKS:")
        for task in high_risk[:5]:
            print(f"    ⚠️  {task['id']}: {task['description'][:40]}")
            print(
                f"       Range: {task['optimistic']:.1f}h - {task['pessimistic']:.1f}h (uncertainty: {task['uncertainty_ratio'] * 100:.0f}%)"
            )

    if verbose:
        print(f"\n  DETAILED PERCENTILES:")
        for p, val in results["percentiles"].items():
            print(f"    {p.upper()}: {val:.1f}h")

        if chart:
            print(f"\n  DISTRIBUTION (histogram):")
            histogram = generate_histogram_data(results, bins=15)
            max_count = max(h["count"] for h in histogram) if histogram else 1
            for h in histogram:
                bar_len = int(h["count"] / max_count * 40)
                print(
                    f"    {h['range']:>12} | {'█' * bar_len} ({h['probability']:.1f}%)"
                )

    if output_file:
        output = {k: v for k, v in results.items() if k != "_raw_results"}
        output["high_risk_tasks"] = high_risk
        with open(output_file, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\n  Results saved to: {output_file}")

    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    main()
