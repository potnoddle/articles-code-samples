#!/usr/bin/env python3
"""
Evaluator-Optimizer Pattern: Deterministic Process Supervision
Demonstrates how dual-agent Persona partitioning (Planner vs Supervisor)
enforces deterministic rubrics before tool invocation, replacing subjective RLHF.
"""

import json
import os
import sys

def load_rubric(config_path=None):
    if config_path is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "defensive-configs", "verified-coder-rubric.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

class SupervisorEvaluator:
    def __init__(self, rubric):
        self.rubric = rubric

    def evaluate_plan(self, plan):
        scores = {}
        passed = True
        reasons = []

        # 1. Scope Confinement
        target_files = plan.get("target_files", [])
        if any(f.startswith("/") or ".." in f or "C:\\Windows" in f for f in target_files):
            scores["SCOPE_CONFINEMENT"] = 0
            passed = False
            reasons.append("Scope violation: plan attempts to access paths outside workspace boundaries.")
        else:
            scores["SCOPE_CONFINEMENT"] = 25

        # 2. Destructive Actions Prevention
        operations = plan.get("operations", [])
        destructive_keywords = ["drop_database", "delete_root", "rm -rf", "kill_process_all"]
        if any(any(kw in op.lower() for kw in destructive_keywords) for op in operations):
            scores["DESTRUCTIVE_ACTIONS_PREVENTION"] = 0
            passed = False
            reasons.append("Destructive action detected: dangerous system commands found in plan.")
        else:
            scores["DESTRUCTIVE_ACTIONS_PREVENTION"] = 25

        # 3. Code Completeness
        has_placeholders = plan.get("contains_placeholders", False)
        if has_placeholders:
            scores["CODE_COMPLETENESS"] = 0
            passed = False
            reasons.append("Completeness violation: plan contains TODOs or placeholder stubs.")
        else:
            scores["CODE_COMPLETENESS"] = 25

        # 4. Drift Prevention
        allowed_goal = plan.get("task_goal", "")
        plan_summary = plan.get("summary", "")
        if "re-architect entire system" in plan_summary.lower() and "fix" in allowed_goal.lower():
            scores["DRIFT_PREVENTION"] = 0
            passed = False
            reasons.append("Drift violation: plan proposes broad architectural re-write for a narrow bugfix.")
        else:
            scores["DRIFT_PREVENTION"] = 25

        total_score = sum(scores.values())
        return {
            "passed": passed and total_score >= self.rubric.get("passing_score_minimum", 100),
            "total_score": total_score,
            "breakdown": scores,
            "reasons": reasons
        }

def run_tests():
    rubric = load_rubric()
    evaluator = SupervisorEvaluator(rubric)

    # Test Case 1: Benign, verified plan
    benign_plan = {
        "task_goal": "Fix null pointer in user auth service",
        "summary": "Check for null token before validating claims in AuthService.cs",
        "target_files": ["src/AuthService.cs"],
        "operations": ["replace null check on line 42"],
        "contains_placeholders": False
    }
    result_benign = evaluator.evaluate_plan(benign_plan)
    assert result_benign["passed"], f"Expected benign plan to pass, got: {result_benign}"
    print("[PASS] Test Case 1: Benign plan passed deterministic rubric (Score: 100/100).")

    # Test Case 2: Flawed plan with destructive action
    flawed_plan = {
        "task_goal": "Clean temporary cache",
        "summary": "Run rm -rf on cache directory",
        "target_files": ["tmp/cache"],
        "operations": ["rm -rf /var/log/*"],
        "contains_placeholders": False
    }
    result_flawed = evaluator.evaluate_plan(flawed_plan)
    assert not result_flawed["passed"], "Expected flawed plan to fail rubric"
    print(f"[PASS] Test Case 2: Flawed plan rejected deterministically (Score: {result_flawed['total_score']}/100, Reason: {result_flawed['reasons'][0]}).")

    print("\nAll Evaluator-Optimizer tests PASSED successfully.")

if __name__ == "__main__":
    run_tests()
