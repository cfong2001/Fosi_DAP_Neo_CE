#!/usr/bin/env python3
"""Validate the shape and explicit evidence limits of the CE status ledger."""
import json
from pathlib import Path

LEVELS = ("source_review", "emulation", "combined_build", "hardware")
STATES = {"verified", "incomplete", "issues_found", "not_run"}


def validate(ledger):
    errors = []
    if ledger.get("schema") != 1 or ledger.get("levels") != list(LEVELS):
        errors.append("unsupported schema or evidence levels")
    if not isinstance(ledger.get("scope"), str) or not ledger["scope"].strip():
        errors.append("scope is required")
    features = ledger.get("features")
    if not isinstance(features, list) or not features:
        return errors + ["features must be a nonempty list"]
    seen = set()
    for feature in features:
        if not isinstance(feature, dict):
            errors.append("feature must be an object")
            continue
        ident = feature.get("id")
        if not isinstance(ident, str) or not ident or ident in seen:
            errors.append(f"missing or duplicate feature id: {ident!r}")
        else:
            seen.add(ident)
        if not isinstance(feature.get("name"), str) or not feature["name"].strip():
            errors.append(f"{ident}: name is required")
        if not isinstance(feature.get("evidence"), str) or not feature["evidence"].strip():
            errors.append(f"{ident}: evidence and limitations are required")
        status = feature.get("status")
        if not isinstance(status, dict) or set(status) != set(LEVELS):
            errors.append(f"{ident}: exactly four evidence levels are required")
            continue
        for level in LEVELS:
            if not isinstance(status[level], str) or status[level] not in STATES:
                errors.append(f"{ident}: invalid {level} status")
    return errors


def main():
    path = Path(__file__).with_name("feature-evidence.json")
    ledger = json.loads(path.read_text(encoding="utf-8"))
    errors = validate(ledger)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Evidence ledger: {len(ledger['features'])} entries; "
          "statuses are declarations, not proof of device behavior.")


if __name__ == "__main__":
    main()
