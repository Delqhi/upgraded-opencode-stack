#!/usr/bin/env python3
"""
Plan JSON Schema Validator v2.0
Validates plan files against the /plan v2 JSON Schema.

Usage:
    python3 plan_validate.py <plan.json> [--strict] [--verbose]

Exit codes:
    0 - Plan is valid
    1 - Plan has errors (details printed)
    2 - File not found or parse error
"""

import json
import sys
import os
from typing import Any

REQUIRED_SECTIONS = [
    "version",
    "id",
    "title",
    "mode",
    "created",
    "status",
    "outcomes",
    "current_state",
    "phases",
    "done_criteria",
]

RECOMMENDED_SECTIONS = [
    "decisions",
    "assumptions",
    "dependency_graph",
    "risks",
    "rollback_plan",
    "approvals",
    "metrics",
    "learning",
]

VALID_MODES = [
    "plan-only",
    "plan-and-execute",
    "resume-approved-plan",
    "continuous-planning",
]
VALID_STATUSES = ["draft", "approved", "in-progress", "completed", "re-planned"]
VALID_PRIORITIES = ["critical", "high", "medium", "optional"]


def validate_plan(plan: dict, strict: bool = False) -> list[str]:
    """Validate a plan dictionary against the schema rules."""
    errors = []
    warnings = []

    # Required top-level fields
    for field in REQUIRED_SECTIONS:
        if field not in plan:
            errors.append(f"MISSING: Required field '{field}' is missing")

    # Recommended fields
    if not strict:
        for field in RECOMMENDED_SECTIONS:
            if field not in plan:
                warnings.append(
                    f"RECOMMENDED: Field '{field}' is missing (not required but recommended)"
                )

    # Version check
    if plan.get("version"):
        if not plan["version"].startswith("2."):
            errors.append(f"INVALID: Version must be 2.x.x, got '{plan['version']}'")

    # Mode validation
    mode = plan.get("mode", "")
    if mode and mode not in VALID_MODES:
        errors.append(f"INVALID: Mode must be one of {VALID_MODES}, got '{mode}'")

    # Status validation
    status = plan.get("status", "")
    if status and status not in VALID_STATUSES:
        errors.append(
            f"INVALID: Status must be one of {VALID_STATUSES}, got '{status}'"
        )

    # Outcomes validation
    outcomes = plan.get("outcomes", {})
    if outcomes:
        if "objective" not in outcomes:
            errors.append("MISSING: outcomes.objective is required")
        if "key_results" not in outcomes or not outcomes.get("key_results"):
            errors.append(
                "MISSING: outcomes.key_results must have at least one key result"
            )
        else:
            for i, kr in enumerate(outcomes["key_results"]):
                if "metric" not in kr:
                    errors.append(
                        f"MISSING: outcomes.key_results[{i}].metric is required"
                    )
                if "target" not in kr:
                    errors.append(
                        f"MISSING: outcomes.key_results[{i}].target is required"
                    )

    # Phases validation
    phases = plan.get("phases", [])
    if not phases:
        errors.append("MISSING: At least one phase is required")
    else:
        if len(phases) > 3:
            errors.append(f"INVALID: Maximum 3 phases allowed, got {len(phases)}")

        for phase_idx, phase in enumerate(phases):
            phase_id = phase.get("id", f"P{phase_idx + 1}")

            if "name" not in phase:
                errors.append(f"MISSING: phases[{phase_idx}].name is required")

            if "priority" in phase and phase["priority"] not in VALID_PRIORITIES:
                errors.append(
                    f"INVALID: phases[{phase_idx}].priority must be one of {VALID_PRIORITIES}"
                )

            tasks = phase.get("tasks", [])
            if not tasks:
                errors.append(
                    f"MISSING: phases[{phase_idx}].tasks must have at least one task"
                )

            for task_idx, task in enumerate(tasks):
                task_id = task.get("id", f"{phase_id}-T{task_idx + 1}")

                if "description" not in task:
                    errors.append(f"MISSING: {task_id}.description is required")

                # 3-Point estimation check
                effort = task.get("effort", {})
                if effort:
                    for estimate_type in ["pessimistic", "realistic", "optimistic"]:
                        if estimate_type not in effort:
                            errors.append(
                                f"MISSING: {task_id}.effort.{estimate_type} is required"
                            )

                if "validation" not in task:
                    errors.append(f"MISSING: {task_id}.validation is required")

    # Dependency graph validation
    dep_graph = plan.get("dependency_graph", {})
    if dep_graph:
        nodes = dep_graph.get("nodes", [])
        edges = dep_graph.get("edges", [])

        # Check that all edge targets exist in nodes
        node_set = set(nodes)
        for edge_idx, edge in enumerate(edges):
            if "from" not in edge or "to" not in edge:
                errors.append(
                    f"MISSING: dependency_graph.edges[{edge_idx}] must have 'from' and 'to'"
                )
            else:
                if edge["from"] not in node_set:
                    errors.append(
                        f"INVALID: dependency_graph.edges[{edge_idx}].from '{edge['from']}' not in nodes"
                    )
                if edge["to"] not in node_set:
                    errors.append(
                        f"INVALID: dependency_graph.edges[{edge_idx}].to '{edge['to']}' not in nodes"
                    )

        # Check for cycles (simple DFS)
        adj = {}
        for edge in edges:
            if "from" in edge and "to" in edge:
                adj.setdefault(edge["from"], []).append(edge["to"])

        def has_cycle(node, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.discard(node)
            return False

        visited = set()
        for node in nodes:
            if node not in visited:
                if has_cycle(node, visited, set()):
                    errors.append(
                        "INVALID: dependency_graph contains a cycle (must be a DAG)"
                    )
                    break

    # Risk validation
    risks = plan.get("risks", [])
    for risk_idx, risk in enumerate(risks):
        risk_id = risk.get("id", f"R{risk_idx + 1}")

        if "likelihood" in risk:
            likelihood = risk["likelihood"]
            if not (0.0 <= likelihood <= 1.0):
                errors.append(
                    f"INVALID: {risk_id}.likelihood must be between 0.0 and 1.0, got {likelihood}"
                )

        if "impact" in risk:
            impact = risk["impact"]
            if not (1 <= impact <= 10):
                errors.append(
                    f"INVALID: {risk_id}.impact must be between 1 and 10, got {impact}"
                )

        # Check risk score calculation
        if "likelihood" in risk and "impact" in risk:
            expected_score = risk["likelihood"] * risk["impact"]
            actual_score = risk.get("score", 0)
            if abs(expected_score - actual_score) > 0.1:
                warnings.append(
                    f"MISMATCH: {risk_id}.score should be ~{expected_score:.1f}, got {actual_score}"
                )

    # Done criteria validation
    done_criteria = plan.get("done_criteria", [])
    if not done_criteria:
        errors.append("MISSING: At least one done criterion is required")

    # Overall risk score
    overall_risk = plan.get("overall_risk_score")
    if overall_risk is not None:
        if not (0 <= overall_risk <= 100):
            errors.append(
                f"INVALID: overall_risk_score must be between 0 and 100, got {overall_risk}"
            )
        elif overall_risk > 60:
            warnings.append(
                f"WARNING: overall_risk_score is {overall_risk} (>60 = CRITICAL, should re-plan)"
            )

    # Plan quality score
    quality_score = plan.get("plan_quality_score")
    if quality_score is not None:
        if not (0 <= quality_score <= 100):
            errors.append(
                f"INVALID: plan_quality_score must be between 0 and 100, got {quality_score}"
            )
        elif quality_score < 70:
            warnings.append(
                f"WARNING: plan_quality_score is {quality_score} (<70 = needs improvement)"
            )

    # Rollback plan
    rollback = plan.get("rollback_plan", {})
    if rollback:
        for field in ["trigger", "action", "max_loss"]:
            if field not in rollback:
                warnings.append(f"RECOMMENDED: rollback_plan.{field} is recommended")

    return errors, warnings


def calculate_quality_score(plan: dict) -> dict[str, int]:
    """Calculate plan quality score (0-100) based on completeness."""
    scores = {
        "completeness": 0,
        "clarity": 0,
        "risk_coverage": 0,
        "estimation_quality": 0,
        "dependency_modeling": 0,
        "outcome_alignment": 0,
    }

    # Completeness (0-25)
    required_fields = REQUIRED_SECTIONS
    present = sum(1 for f in required_fields if f in plan)
    scores["completeness"] = int((present / len(required_fields)) * 25)

    # Clarity (0-20)
    clarity_checks = 0
    total_tasks = 0
    tasks_with_validation = 0
    for phase in plan.get("phases", []):
        for task in phase.get("tasks", []):
            total_tasks += 1
            if task.get("validation"):
                tasks_with_validation += 1
    if total_tasks > 0:
        clarity_checks = tasks_with_validation / total_tasks
    scores["clarity"] = int(clarity_checks * 20)

    # Risk Coverage (0-20)
    risks = plan.get("risks", [])
    risks_with_mitigation = sum(1 for r in risks if r.get("mitigation"))
    if risks:
        scores["risk_coverage"] = int((risks_with_mitigation / len(risks)) * 20)
    elif plan.get("overall_risk_score") == 0:
        scores["risk_coverage"] = 10  # Partial credit for explicit zero risk

    # Estimation Quality (0-15)
    tasks_with_estimates = 0
    tasks_with_3point = 0
    for phase in plan.get("phases", []):
        for task in phase.get("tasks", []):
            effort = task.get("effort", {})
            if effort:
                tasks_with_estimates += 1
                if all(k in effort for k in ["pessimistic", "realistic", "optimistic"]):
                    tasks_with_3point += 1
    total_tasks = max(1, tasks_with_estimates)
    scores["estimation_quality"] = int((tasks_with_3point / total_tasks) * 15)

    # Dependency Modeling (0-10)
    dep_graph = plan.get("dependency_graph", {})
    if (
        dep_graph.get("nodes")
        and dep_graph.get("edges")
        and dep_graph.get("critical_path")
    ):
        scores["dependency_modeling"] = 10
    elif dep_graph.get("nodes") and dep_graph.get("edges"):
        scores["dependency_modeling"] = 5
    elif dep_graph.get("nodes"):
        scores["dependency_modeling"] = 3

    # Outcome Alignment (0-10)
    outcomes = plan.get("outcomes", {})
    if outcomes.get("objective") and outcomes.get("key_results"):
        scores["outcome_alignment"] = 10
    elif outcomes.get("objective"):
        scores["outcome_alignment"] = 5

    total = sum(scores.values())
    return {**scores, "total": total}


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 plan_validate.py <plan.json> [--strict] [--verbose]")
        sys.exit(2)

    plan_file = sys.argv[1]
    strict = "--strict" in sys.argv
    verbose = "--verbose" in sys.argv

    if not os.path.exists(plan_file):
        print(f"ERROR: File not found: {plan_file}")
        sys.exit(2)

    try:
        with open(plan_file) as f:
            plan = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}")
        sys.exit(2)

    errors, warnings = validate_plan(plan, strict=strict)
    quality = calculate_quality_score(plan)

    print(f"\n{'=' * 60}")
    print(f"  Plan Validation Report: {plan.get('title', 'Unknown')}")
    print(f"{'=' * 60}")
    print(f"  Version: {plan.get('version', 'N/A')}")
    print(f"  Mode: {plan.get('mode', 'N/A')}")
    print(f"  Status: {plan.get('status', 'N/A')}")
    print(f"  Quality Score: {quality['total']}/100")
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")
    print(f"{'=' * 60}")

    if errors:
        print(f"\n  ERRORS ({len(errors)}):")
        for error in errors:
            print(f"    ❌ {error}")

    if warnings:
        print(f"\n  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"    ⚠️  {warning}")

    if verbose:
        print(f"\n  QUALITY BREAKDOWN:")
        print(f"    Completeness:        {quality['completeness']}/25")
        print(f"    Clarity:             {quality['clarity']}/20")
        print(f"    Risk Coverage:       {quality['risk_coverage']}/20")
        print(f"    Estimation Quality:  {quality['estimation_quality']}/15")
        print(f"    Dependency Modeling: {quality['dependency_modeling']}/10")
        print(f"    Outcome Alignment:   {quality['outcome_alignment']}/10")

    print(f"\n{'=' * 60}")
    if not errors:
        print(f"  ✅ Plan is VALID (Quality: {quality['total']}/100)")
        if quality["total"] >= 85:
            print(f"  🌟 Excellent quality - ready for execution")
        elif quality["total"] >= 70:
            print(f"  👍 Good quality - proceed with noted improvements")
        elif quality["total"] >= 50:
            print(f"  ⚠️  Needs work - fix before review")
        else:
            print(f"  ❌ Unacceptable - re-plan from scratch")
    else:
        print(f"  ❌ Plan is INVALID - {len(errors)} error(s) must be fixed")
    print(f"{'=' * 60}\n")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
