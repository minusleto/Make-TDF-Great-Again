#!/usr/bin/env python3
"""Validate Aral full-cash costs against shared generic TDF treasury labels.

The focused Aral snapshot intentionally does not copy the shared MD_decisions localisation.
These keys are supplied by the parent TDF installation.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DECISIONS = Path("common/decisions/aral_sea_decisions.txt")
GENERIC_TREASURY_COST_KEYS = frozenset({
    "cost_0_5", "cost_1_0", "cost_1_5", "cost_3_0", "cost_4_0", "cost_4_5",
    "cost_7_5", "cost_8_0", "cost_10_0", "cost_25_0", "cost_40_0", "cost_50_0",
})


def matching_brace(text: str, opening: int) -> int:
    depth = 0
    quoted = False
    escaped = False
    comment = False
    for index in range(opening, len(text)):
        char = text[index]
        if comment:
            if char == "\n":
                comment = False
            continue
        if quoted:
            if escaped:
                escaped = False
            elif char == chr(92):
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == "#":
            comment = True
        elif char == '"':
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("unclosed decision block")


def decision_blocks(text: str) -> dict[str, str]:
    result = {}
    pattern = re.compile(r"(?m)^[ \t]+(aral_[A-Za-z0-9_]+)\s*=\s*\{")
    for match in pattern.finditer(text):
        opening = text.find("{", match.start(), match.end())
        closing = matching_brace(text, opening)
        name = match.group(1)
        if name in result:
            raise ValueError("duplicate decision block " + name)
        result[name] = text[opening + 1:closing]
    return result


def inner(text: str, name: str) -> str | None:
    match = re.search(r"\b" + re.escape(name) + r"\s*=\s*\{", text)
    if not match:
        return None
    opening = match.end() - 1
    closing = matching_brace(text, opening)
    return text[opening + 1:closing]


def expected_key(amount: float) -> str:
    return "cost_" + format(amount, ".1f").replace(".", "_")


def validate_costs(text: str) -> list[str]:
    decisions = decision_blocks(text)
    findings = []
    if not decisions:
        return ["no Aral decision blocks found"]

    for decision, body in decisions.items():
        area = decision + ": "
        labels = re.findall(r"custom_cost_text\s*=\s*([A-Za-z0-9_.-]+)", body)
        trigger = inner(body, "custom_cost_trigger")
        complete = inner(body, "complete_effect") or ""
        debits = re.findall(r"treasury_change\s*=\s*(-?[\d.]+)", complete)
        treasury_effects = re.findall(r"modify_treasury_effect\s*=\s*yes", complete)

        if len(labels) != 1:
            findings.append(area + "expected exactly one custom_cost_text")
        elif labels[0] not in GENERIC_TREASURY_COST_KEYS:
            findings.append(area + "unverified or project-local cost key " + labels[0])

        if trigger is not None:
            findings.append(area + "remove custom_cost_trigger; custom_cost_text displays the price without a treasury-balance gate")
        if re.search(r"\btreasury\s*>", body):
            findings.append(area + "treasury-balance affordability check remains")

        if len(debits) != 1 or len(treasury_effects) != 1:
            findings.append(area + "must charge one full cash amount with one treasury_change and one modify_treasury_effect")
        else:
            amount = float(debits[0])
            if amount >= 0:
                findings.append(area + "treasury_change must be negative")
            elif len(labels) == 1 and labels[0] != expected_key(abs(amount)):
                findings.append(area + "price key %s does not match full treasury debit %s" % (labels[0], abs(amount)))

        if re.search(r"debt_change\s*=|modify_debt_effect\s*=\s*yes", body):
            findings.append(area + "explicit debt transaction duplicates the TDF automatic negative-treasury financing")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mod_root", type=Path, help="path to the Aral mdredux folder")
    args = parser.parse_args()
    path = args.mod_root / DECISIONS
    try:
        text = path.read_text(encoding="utf-8-sig")
        findings = validate_costs(text)
    except (OSError, UnicodeError, ValueError) as error:
        print("ERROR:", error, file=sys.stderr)
        return 2

    if findings:
        for finding in findings:
            print("ERROR:", finding)
        return 1
    print("Verified %d Aral decisions: shared generic cost keys match full treasury debits; no cash-balance gates or explicit debt charges." % len(decision_blocks(text)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
