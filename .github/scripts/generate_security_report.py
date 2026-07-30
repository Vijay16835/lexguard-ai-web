#!/usr/bin/env python3
"""
LexGuard AI – Security Report Aggregator
Collects Bandit, Safety, pip-audit outputs into a unified JSON summary.
"""

import argparse
import json
import os
from datetime import datetime


def load_json_safe(path: str) -> dict | list | None:
    if not path or not os.path.isfile(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        print(f"  [WARN] Could not parse {path}: {e}")
        return None


def parse_bandit(data) -> dict:
    if not data or not isinstance(data, dict):
        return {"issues": [], "totals": {}}
    results = data.get("results", [])
    metrics = data.get("metrics", {}).get("_totals", {})
    issues = []
    for r in results:
        issues.append({
            "filename": r.get("filename", ""),
            "line":     r.get("line_number", 0),
            "severity": r.get("issue_severity", "").upper(),
            "confidence": r.get("issue_confidence", "").upper(),
            "text":     r.get("issue_text", ""),
            "test_id":  r.get("test_id", ""),
            "test_name": r.get("test_name", ""),
        })
    totals = {
        "total_issues": len(results),
        "high":   metrics.get("SEVERITY.HIGH", 0),
        "medium": metrics.get("SEVERITY.MEDIUM", 0),
        "low":    metrics.get("SEVERITY.LOW", 0),
    }
    return {"issues": issues, "totals": totals}


def parse_safety(data) -> dict:
    vulns = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("vulnerabilities", data.get("report", []))
    else:
        return {"vulnerabilities": [], "total": 0}
    for item in items:
        if isinstance(item, dict):
            vulns.append({
                "package":     item.get("package_name", item.get("name", "")),
                "version":     item.get("analyzed_version", item.get("version", "")),
                "vuln_id":     item.get("vulnerability_id", item.get("id", "")),
                "severity":    item.get("severity", "UNKNOWN").upper(),
                "description": item.get("advisory", item.get("description", ""))[:200],
            })
    return {"vulnerabilities": vulns, "total": len(vulns)}


def parse_pip_audit(data) -> dict:
    if not isinstance(data, list):
        data = []
    vulns = []
    for pkg in data:
        for v in pkg.get("vulns", []):
            vulns.append({
                "package":     pkg.get("name", ""),
                "version":     pkg.get("version", ""),
                "vuln_id":     v.get("id", ""),
                "fix_versions": v.get("fix_versions", []),
                "description": v.get("description", "")[:200],
            })
    return {"vulnerabilities": vulns, "total": len(vulns)}


def determine_overall_status(bandit_totals: dict, safety_total: int, audit_total: int) -> str:
    if bandit_totals.get("high", 0) > 0 or safety_total > 5 or audit_total > 5:
        return "CRITICAL"
    if bandit_totals.get("medium", 0) > 3 or safety_total > 0 or audit_total > 0:
        return "NEEDS_REVIEW"
    return "PASSED"


def main():
    parser = argparse.ArgumentParser(description="LexGuard Security Report Aggregator")
    parser.add_argument("--bandit",    default="", help="Path to bandit JSON report")
    parser.add_argument("--safety",    default="", help="Path to safety JSON report")
    parser.add_argument("--pip-audit", default="", help="Path to pip-audit JSON report")
    parser.add_argument("--output",    default="test-results/security/security-summary.json")
    args = parser.parse_args()

    print("🔒 Aggregating Security Reports...")

    bandit_raw  = load_json_safe(args.bandit)
    safety_raw  = load_json_safe(args.safety)
    audit_raw   = load_json_safe(getattr(args, "pip_audit", ""))

    bandit_result = parse_bandit(bandit_raw)
    safety_result = parse_safety(safety_raw)
    audit_result  = parse_pip_audit(audit_raw if isinstance(audit_raw, list) else [])

    overall = determine_overall_status(
        bandit_result["totals"],
        safety_result["total"],
        audit_result["total"],
    )

    summary = {
        "generated_at":  datetime.now().isoformat(),
        "project":       "LexGuard AI",
        "overall_status": overall,
        "tools": {
            "bandit": {
                "available": bandit_raw is not None,
                "totals":    bandit_result["totals"],
                "issues":    bandit_result["issues"][:50],  # cap at 50 for readability
            },
            "safety": {
                "available":       safety_raw is not None,
                "total":           safety_result["total"],
                "vulnerabilities": safety_result["vulnerabilities"][:20],
            },
            "pip_audit": {
                "available":       audit_raw is not None,
                "total":           audit_result["total"],
                "vulnerabilities": audit_result["vulnerabilities"][:20],
            },
        },
    }

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"  Overall Status: {overall}")
    print(f"  Bandit Issues : {bandit_result['totals'].get('total_issues', 0)}")
    print(f"  Safety Vulns  : {safety_result['total']}")
    print(f"  pip-audit     : {audit_result['total']}")
    print(f"  Report written: {args.output}")


if __name__ == "__main__":
    main()
