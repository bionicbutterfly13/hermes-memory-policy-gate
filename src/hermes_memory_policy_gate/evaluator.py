from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .policy import decide_memory_policy


def evaluate_cases(path: str | Path) -> dict[str, Any]:
    scenario_path = Path(path)
    data = json.loads(scenario_path.read_text(encoding="utf-8"))
    cases = data.get("cases", data if isinstance(data, list) else [])
    results = []
    passed = 0
    dry_run_only = True
    for case in cases:
        decision = decide_memory_policy(case.get("request", case)).to_dict()
        dry_run_only = dry_run_only and bool(decision["dry_run"])
        expected = case.get("expected_tier")
        checks = {"tier": decision["tier"] == expected}
        optional_expectations = {
            "blocked": "expected_blocked",
            "enforced": "expected_enforced",
            "enforcement_action": "expected_enforcement_action",
            "dry_run": "expected_dry_run",
            "would_mutate": "expected_would_mutate",
            "approval_required": "expected_approval_required",
        }
        for field, expected_key in optional_expectations.items():
            if expected_key in case:
                checks[field] = decision[field] == case[expected_key]
        ok = all(checks.values())
        passed += int(ok)
        live_write_intent = bool(
            case.get("live_write_intent")
            or decision.get("dry_run") is False
            or case.get("request", case).get("metadata", {}).get("live_write_intent")
        )
        results.append({
            "name": case.get("name", "unnamed"),
            "ok": ok,
            "expected_tier": expected,
            "actual_tier": decision["tier"],
            "confidence": decision["confidence"],
            "reason_codes": decision["reason_codes"],
            "approval_required": decision["approval_required"],
            "dry_run": decision["dry_run"],
            "would_mutate": decision["would_mutate"],
            "blocked": decision["blocked"],
            "enforced": decision["enforced"],
            "enforcement_action": decision["enforcement_action"],
            "live_write_intent": live_write_intent,
            "checks": checks,
        })
    return {
        "scenario_file": str(scenario_path),
        "passed": passed,
        "failed": len(results) - passed,
        "total": len(results),
        "results": results,
        "live_writes": False,
        "live_write_intents": sum(1 for item in results if item["live_write_intent"]),
        "blocked_write_intents": sum(1 for item in results if item["live_write_intent"] and item["blocked"]),
        "advisory_write_intents": sum(1 for item in results if item["live_write_intent"] and not item["blocked"]),
        "dry_run_only": dry_run_only,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate Hermes memory policy routing scenarios.")
    parser.add_argument("scenario_file")
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    args = parser.parse_args(argv)
    report = evaluate_cases(args.scenario_file)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"{report['passed']}/{report['total']} passed — dry_run_only={report['dry_run_only']}")
        for item in report["results"]:
            mark = "PASS" if item["ok"] else "FAIL"
            print(f"{mark} {item['name']}: expected={item['expected_tier']} actual={item['actual_tier']}")
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
