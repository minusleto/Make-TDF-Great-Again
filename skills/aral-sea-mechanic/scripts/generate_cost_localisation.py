#!/usr/bin/env python3
"""Generate Aral's project-local blocked-label and hover-tooltip localisation variants.

The MDC wiki does not document automatic engine lookup for these suffixes. Default mode is
check-only. Pass --write to append missing keys without rewriting existing translations.
Values are derived from each decision's custom_cost_text and its existing <decision>_cost_tt.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DECISIONS = Path("mdredux/common/decisions/aral_sea_decisions.txt")
ENGLISH = Path("mdredux/localisation/english/aral_sea_l_english.yml")
RUSSIAN = Path("mdredux/localisation/russian/aral_sea_l_russian.yml")
BOM = b"\xef\xbb\xbf"


def matching_brace(text: str, open_index: int) -> int:
    depth = 0
    quoted = False
    escaped = False
    comment = False
    for index in range(open_index, len(text)):
        char = text[index]
        if comment:
            if char == "\n":
                comment = False
            continue
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
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


def decision_cost_keys(text: str) -> list[tuple[str, str]]:
    """Return (decision_id, custom_cost_text key) in source order."""
    output = []
    pattern = re.compile(r"(?m)^\t(aral_[A-Za-z0-9_]+)\s*=\s*\{")
    for match in pattern.finditer(text):
        open_index = text.find("{", match.start(), match.end())
        close_index = matching_brace(text, open_index)
        body = text[open_index + 1:close_index]
        cost = re.search(r"(?m)^\s*custom_cost_text\s*=\s*([A-Za-z0-9_.-]+)", body)
        if cost:
            output.append((match.group(1), cost.group(1)))
    if not output:
        raise ValueError("no Aral decisions with custom_cost_text were found")
    keys = [key for _, key in output]
    if len(keys) != len(set(keys)):
        raise ValueError("custom_cost_text keys must be unique for this generator")
    return output


def parse_localisation(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    pattern = re.compile(r'^ ([A-Za-z0-9_.-]+):\s*"((?:[^"\\]|\\.)*)"$')
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = pattern.match(line)
        if not match:
            continue
        key, value = match.groups()
        if key in result:
            raise ValueError("duplicate localisation key %s at line %d" % (key, line_number))
        result[key] = value
    return result


def generate_entries(decisions_text: str, localisations: dict[str, str]) -> dict[str, dict[str, str]]:
    """Build expected keys for each language; _tooltip mirrors the established full cost tooltip."""
    decisions = decision_cost_keys(decisions_text)
    parsed = {lang: parse_localisation(text) for lang, text in localisations.items()}
    result: dict[str, dict[str, str]] = {}
    for lang, keys in parsed.items():
        generated: dict[str, str] = {}
        for decision, cost_key in decisions:
            base = keys.get(cost_key)
            tooltip = keys.get(decision + "_cost_tt")
            if base is None:
                raise ValueError("%s: missing base cost key %s" % (lang, cost_key))
            if tooltip is None:
                raise ValueError("%s: missing full cost tooltip %s_cost_tt" % (lang, decision))
            generated[cost_key + "_blocked"] = "§R" + base + "§!"
            generated[cost_key + "_tooltip"] = tooltip
        result[lang] = generated
    return result


def merge_missing_keys(text: str, generated: dict[str, str], lang: str) -> tuple[str, list[str]]:
    current = parse_localisation(text)
    missing = []
    for key, value in generated.items():
        if key in current and current[key] != value:
            raise ValueError("%s: existing key %s differs from generated output; review manually" % (lang, key))
        if key not in current:
            missing.append(' %s: "%s"' % (key, value))
    if not missing:
        return text, []
    prefix = "" if text.endswith("\n") else "\n"
    return text + prefix + "\n" + "\n".join(missing) + "\n", missing


def read_localisation(path: Path) -> tuple[bytes, str]:
    raw = path.read_bytes()
    has_bom = BOM if raw.startswith(BOM) else b""
    text = raw.decode("utf-8-sig")
    return has_bom, text.replace("\r\n", "\n").replace("\r", "\n")


def write_localisation(path: Path, bom: bytes, text: str) -> None:
    raw = bom + text.replace("\n", "\r\n").encode("utf-8")
    path.write_bytes(raw)


def run(root: Path, write: bool) -> int:
    decisions_path = root / DECISIONS
    if not decisions_path.is_file():
        raise FileNotFoundError(decisions_path)
    decisions_text = decisions_path.read_text(encoding="utf-8-sig")
    paths = {"en": root / ENGLISH, "ru": root / RUSSIAN}
    source_text = {}
    bom_map = {}
    for lang, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(path)
        bom_map[lang], source_text[lang] = read_localisation(path)
    generated = generate_entries(decisions_text, source_text)
    missing_total = 0
    for lang, path in paths.items():
        updated, missing = merge_missing_keys(source_text[lang], generated[lang], lang)
        missing_total += len(missing)
        if missing:
            action = "write" if write else "missing"
            print("%s: %s (%d keys)" % (lang, action, len(missing)))
            for line in missing:
                print(line)
            if write:
                write_localisation(path, bom_map[lang], updated)
    if missing_total and not write:
        print("Check failed: run with --write to append generated keys.")
        return 1
    print("Generated cost localisation is up to date." if not missing_total else "Generated %d localisation keys." % missing_total)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root (defaults to this checkout)")
    parser.add_argument("--write", action="store_true", help="append missing EN/RU variants")
    args = parser.parse_args()
    try:
        return run(args.root.resolve(), args.write)
    except (OSError, UnicodeError, ValueError) as error:
        print("ERROR:", error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
