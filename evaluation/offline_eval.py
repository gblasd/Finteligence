"""
evaluation/offline_eval.py

Layer 5 – Offline evaluation runner.
Runs the golden dataset against the full pipeline BEFORE deployment to
catch regressions in prompt changes, model upgrades, or routing logic.

Usage:
    python -m evaluation.offline_eval
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.security.input_guard import InputGuard
from app.services.query_router import QueryRouter, RouteDestination

_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
_RESULTS_DIR  = Path(__file__).parent / "eval_results"


def run_eval() -> dict:
    """Run offline evaluation against the golden dataset."""
    _RESULTS_DIR.mkdir(exist_ok=True)

    with open(_DATASET_PATH) as f:
        dataset = json.load(f)

    guard  = InputGuard()
    router = QueryRouter()

    results = []
    passed = failed = 0

    for item in dataset:
        qid      = item["id"]
        question = item["question"]
        should_block = item.get("should_be_blocked", False)

        guard_result = guard.check(question)
        route        = router.route(question)

        checks: list[dict] = []

        # Security check
        if should_block:
            ok = not guard_result.is_safe or route == RouteDestination.SECURITY_BLOCK
            checks.append({"name": "security_block", "passed": ok})
        else:
            checks.append({"name": "input_safe", "passed": guard_result.is_safe})

        item_passed = all(c["passed"] for c in checks)
        if item_passed:
            passed += 1
        else:
            failed += 1

        results.append({
            "id":        qid,
            "question":  question,
            "checks":    checks,
            "passed":    item_passed,
        })
        status = "✅" if item_passed else "❌"
        print(f"{status} [{qid}] {question[:60]}")

    summary = {
        "timestamp": datetime.utcnow().isoformat(),
        "total":     len(dataset),
        "passed":    passed,
        "failed":    failed,
        "pass_rate": f"{passed/len(dataset)*100:.1f}%",
        "results":   results,
    }

    # Save results
    ts   = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = _RESULTS_DIR / f"eval_{ts}.json"
    with open(path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nResults: {passed}/{len(dataset)} passed ({summary['pass_rate']})")
    print(f"Saved to: {path}")
    return summary


if __name__ == "__main__":
    run_eval()
