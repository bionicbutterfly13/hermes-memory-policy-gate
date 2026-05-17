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
    for case in cases:
        decision = decide_memory_policy(case.get("request", case)).to_dict()
        expected = case.get("expected_tier")
        ok = decision["tier"] == expected
        passed += int(ok)
        results.append({
            "name": case.get("name", "unnamed"),
            "ok": ok,
            "expected_tier": expected,
            "actual_tier": decision["tier"],
            "confidence": decision["confidence"],
            "reason_codes": decision["reason_codes"],
        })
    return {
        "scenario_file": str(scenario_path),
        "passed": passed,
        "failed": len(results) - passed,
        "total": len(results),
        "results": results,
        "live_writes": False,
        "dry_run_only": True,
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
