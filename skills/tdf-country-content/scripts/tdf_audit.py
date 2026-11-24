#!/usr/bin/env python3
"""Статический аудит контента стран TDF/MDC по правилам tdf-country-content.

Запуск из корня репозитория:
    python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --require-external-registry
    python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --tags POR,KAZ
    python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --details KAZ
    python3 -I skills/tdf-country-content/scripts/tdf_audit.py . --json audit.json

Скрипт не запускает HOI4 и не содержит базовый мод. Ссылки на отсутствующие в
срезе внешние namespace/идеи не объявляются ошибками без достаточных оснований.
Код завершения: 0 — ERROR нет; 1 — найдены ERROR; 2 — ошибка входных файлов/репозитория.
Тесты: python -m unittest discover -s skills/tdf-country-content/tests -v
"""
import argparse
import json
import re
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Sequence, Tuple, Union

BANNED = [
    "strengthen ties", "mutual benefit", "significant", "foothold", "valuable",
    "comprehensive", "ensuring", "foster", "paving the way",
]
BANNED_WORD = re.compile(r"\bkey\b", re.I)
GENERIC_LABELS = {
    "good", "great", "nice", "excellent", "interesting", "damn", "yes", "no",
    "ok", "okay", "fantastic", "wonderful", "sad", "sure", "decline the proposal",
    "decline", "thanks",
}
TAG_RE = re.compile(r"^[A-Z]{3}$")
LOC_LINE_RE = re.compile(r'^\s*([^\s:#]+):\d*\s+"((?:\\.|[^"\\])*)"\s*(?:#.*)?$')


class AuditInputError(Exception):
    """Ошибка структуры репозитория или чтения входных файлов."""


class Token:
    __slots__ = ("kind", "value", "line", "column", "offset")

    def __init__(self, kind: str, value: str, line: int, column: int, offset: int):
        self.kind = kind
        self.value = value
        self.line = line
        self.column = column
        self.offset = offset


class Entry:
    __slots__ = ("key", "value")

    def __init__(self, key: Token, value: Union[Token, "Block"]):
        self.key = key
        self.value = value

    @property
    def line(self) -> int:
        return self.key.line


class Block:
    __slots__ = ("items", "line")

    def __init__(self, items: Optional[List[Union[Entry, Token]]] = None, line: int = 1):
        self.items = items if items is not None else []
        self.line = line

    @property
    def entries(self) -> List[Entry]:
        return [item for item in self.items if isinstance(item, Entry)]


class ParseIssue:
    __slots__ = ("line", "column", "message")

    def __init__(self, line: int, column: int, message: str):
        self.line = line
        self.column = column
        self.message = message

    def __str__(self) -> str:
        return "line {}:{}: {}".format(self.line, self.column, self.message)


class ParseResult:
    __slots__ = ("root", "issues", "brace_balance")

    def __init__(self, root: Block, issues: List[ParseIssue], brace_balance: int):
        self.root = root
        self.issues = issues
        self.brace_balance = brace_balance


class LocEntry:
    __slots__ = ("key", "value", "path", "line")

    def __init__(self, key: str, value: str, path: str, line: int):
        self.key = key
        self.value = value
        self.path = path
        self.line = line


def read(path: Union[str, Path]) -> str:
    """Read UTF-8 (with optional BOM) without silently replacing bad bytes."""
    p = Path(path)
    try:
        return p.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise AuditInputError("{}: невалидный UTF-8 около байта {}".format(p, exc.start)) from exc
    except OSError as exc:
        raise AuditInputError("{}: {}".format(p, exc)) from exc


def tokenize(text: str) -> Tuple[List[Token], List[ParseIssue]]:
    """Tokenize HOI4 script while respecting comments, escaped quotes and strings."""
    tokens: List[Token] = []
    issues: List[ParseIssue] = []
    i, line, column, n = 0, 1, 1, len(text)

    def advance(chunk: str) -> None:
        nonlocal line, column
        newlines = chunk.count("\n")
        if newlines:
            line += newlines
            column = len(chunk.rsplit("\n", 1)[-1]) + 1
        else:
            column += len(chunk)

    while i < n:
        ch = text[i]
        if ch.isspace():
            advance(ch)
            i += 1
            continue
        if ch == "#":
            end = text.find("\n", i)
            if end < 0:
                advance(text[i:])
                break
            advance(text[i:end])
            i = end
            continue

        start, start_line, start_col = i, line, column
        if ch in "{}=":
            kind = {"{": "LBRACE", "}": "RBRACE", "=": "EQUAL"}[ch]
            tokens.append(Token(kind, ch, start_line, start_col, start))
            advance(ch)
            i += 1
            continue

        if ch == '"':
            i += 1
            advance('"')
            value: List[str] = []
            closed = False
            while i < n:
                cur = text[i]
                if cur == "\\" and i + 1 < n:
                    nxt = text[i + 1]
                    if nxt in ('"', "\\"):
                        value.append(nxt)
                    else:
                        value.append("\\")
                        value.append(nxt)
                    chunk = text[i:i + 2]
                    advance(chunk)
                    i += 2
                    continue
                if cur == '"':
                    advance(cur)
                    i += 1
                    closed = True
                    break
                value.append(cur)
                advance(cur)
                i += 1
            tokens.append(Token("STRING", "".join(value), start_line, start_col, start))
            if not closed:
                issues.append(ParseIssue(start_line, start_col, "незакрытая строка"))
            continue

        while i < n and not text[i].isspace() and text[i] not in '#{}="':
            i += 1
        if i == start:
            issues.append(ParseIssue(line, column, "неожиданный символ {!r}".format(ch)))
            advance(ch)
            i += 1
            continue
        value = text[start:i]
        tokens.append(Token("ATOM", value, start_line, start_col, start))
        advance(value)

    tokens.append(Token("EOF", "", line, column, n))
    return tokens, issues


class HOIParser:
    """Small structural parser for HOI4 key/value files; preserves duplicate keys."""

    def __init__(self, tokens: Sequence[Token], issues: Optional[List[ParseIssue]] = None):
        self.tokens = tokens
        self.pos = 0
        self.issues = issues if issues is not None else []
        self.open_braces = 0
        self.close_braces = 0

    def current(self) -> Token:
        return self.tokens[self.pos]

    def consume(self) -> Token:
        token = self.current()
        if token.kind != "EOF":
            self.pos += 1
        return token

    def parse(self) -> Block:
        return self.parse_items(expect_close=False, opening_line=1)

    def parse_items(self, expect_close: bool, opening_line: int) -> Block:
        block = Block(line=opening_line)
        while self.current().kind != "EOF":
            token = self.current()
            if token.kind == "RBRACE":
                self.close_braces += 1
                self.consume()
                if expect_close:
                    return block
                self.issues.append(ParseIssue(token.line, token.column, "лишняя закрывающая скобка '}'"))
                continue
            if token.kind == "LBRACE":
                self.open_braces += 1
                self.consume()
                child = self.parse_items(expect_close=True, opening_line=token.line)
                block.items.append(Entry(Token("ATOM", "<anonymous>", token.line, token.column, token.offset), child))
                continue
            if token.kind not in ("ATOM", "STRING"):
                self.issues.append(ParseIssue(token.line, token.column, "ожидалось имя параметра, получено {}".format(token.kind)))
                self.consume()
                continue

            key = self.consume()
            if self.current().kind != "EQUAL":
                # Bare values are valid in lists such as search_filters = { FOCUS_FILTER_ECONOMY }.
                block.items.append(key)
                continue
            self.consume()  # '='
            value_token = self.current()
            if value_token.kind == "LBRACE":
                self.consume()
                self.open_braces += 1
                value: Union[Token, Block] = self.parse_items(expect_close=True, opening_line=value_token.line)
            elif value_token.kind in ("ATOM", "STRING"):
                value = self.consume()
            else:
                self.issues.append(ParseIssue(value_token.line, value_token.column, "у параметра {!r} отсутствует значение".format(key.value)))
                continue
            block.items.append(Entry(key, value))

        if expect_close:
            self.issues.append(ParseIssue(opening_line, 1, "блок '{' не закрыт"))
        return block


def parse_hoi(text: str) -> ParseResult:
    tokens, issues = tokenize(text)
    parser = HOIParser(tokens, issues)
    root = parser.parse()
    return ParseResult(root, parser.issues, parser.open_braces - parser.close_braces)


def walk_entries(block: Block) -> Iterator[Entry]:
    for item in block.items:
        if isinstance(item, Entry):
            yield item
            if isinstance(item.value, Block):
                yield from walk_entries(item.value)


def direct_entries(block: Block, key: str) -> List[Entry]:
    return [item for item in block.items if isinstance(item, Entry) and item.key.value == key]


def nested_entries(block: Block, key: str) -> List[Entry]:
    return [entry for entry in walk_entries(block) if entry.key.value == key]


def scalar(entry: Optional[Entry]) -> Optional[str]:
    if entry is not None and isinstance(entry.value, Token):
        return entry.value.value
    return None


def get_scalar(block: Block, key: str) -> Optional[str]:
    for entry in direct_entries(block, key):
        value = scalar(entry)
        if value is not None:
            return value
    return None


def get_block(block: Block, key: str) -> Optional[Block]:
    for entry in direct_entries(block, key):
        if isinstance(entry.value, Block):
            return entry.value
    return None


def find_named_blocks(block: Block, key: str) -> List[Block]:
    return [entry.value for entry in walk_entries(block) if entry.key.value == key and isinstance(entry.value, Block)]


def iter_files(root: Path, suffix: str) -> List[Path]:
    if not root.is_dir():
        return []
    return sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() == suffix.lower())


def detect_tag(parsed: ParseResult) -> Optional[str]:
    """Detect the tree's country selector, not target tags used inside focus logic."""
    tree_blocks = find_named_blocks(parsed.root, "focus_tree") or [parsed.root]
    for tree in tree_blocks:
        country = get_block(tree, "country")
        if country is None:
            continue
        # original_tag identifies the country more explicitly. Both selectors must
        # be read only from the focus_tree country block: nested focus conditions
        # can contain tag = PER/CHI/etc. for strength_ratio and other targets.
        for key in ("original_tag", "tag"):
            for entry in nested_entries(country, key):
                value = scalar(entry)
                if value and TAG_RE.fullmatch(value):
                    return value

    # Older or partial trees may omit a country selector; infer from their own
    # focus IDs rather than mistaking a target tag in an effect/condition for owner.
    focus_ids = []
    for body in find_named_blocks(parsed.root, "focus"):
        fid = get_scalar(body, "id")
        if fid and len(fid) > 4 and fid[3] == "_" and TAG_RE.fullmatch(fid[:3]):
            focus_ids.append(fid[:3])
    return Counter(focus_ids).most_common(1)[0][0] if focus_ids else None


def discover(repo: Union[str, Path]):
    mod = Path(repo) / "mdredux"
    nf = mod / "common" / "national_focus"
    loc_dir = mod / "localisation" / "english"
    ev_dir = mod / "events"
    if not nf.is_dir():
        raise AuditInputError("не найдена директория {}".format(nf))
    if not loc_dir.is_dir():
        raise AuditInputError("не найдена директория {}".format(loc_dir))

    loc_index: Dict[str, List[LocEntry]] = defaultdict(list)
    for path in iter_files(loc_dir, ".yml"):
        for line_no, line in enumerate(read(path).splitlines(), 1):
            match = LOC_LINE_RE.match(line)
            if not match:
                continue
            key, value = match.groups()
            value = value.replace('\\"', '"').replace('\\\\', '\\')
            loc_index[key].append(LocEntry(key, value, str(path), line_no))

    event_files_by_stem: Dict[str, Path] = {}
    for path in iter_files(ev_dir, ".txt"):
        event_files_by_stem.setdefault(path.stem.lower(), path)

    countries = {}
    for path in sorted(nf.rglob("*_Focus_Tree.txt")):
        source = read(path)
        parsed = parse_hoi(source)
        tag = detect_tag(parsed)
        if not tag:
            continue
        stem = path.name[:-len("_Focus_Tree.txt")]
        countries[tag] = {
            "tree": path,
            "tree_source": source,
            "tree_parsed": parsed,
            "events": (
                event_files_by_stem.get(stem.lower())
                or (event_files_by_stem.get("britain") if tag == "ENG" else None)
            ),
        }
    if not countries:
        raise AuditInputError("не удалось обнаружить ни одного *_Focus_Tree.txt с тегом страны в {}".format(nf))
    return countries, loc_index


def build_idea_definition_index(repo, countries):
    """Index visible and hidden idea definitions, including unprefixed legacy IDs."""
    mod = Path(repo) / "mdredux"
    country_tags = set(countries)
    definitions = []
    parse_errors = []
    for path in iter_files(mod / "common" / "ideas", ".txt"):
        parsed = parse_hoi(read(path))
        tags_in_file = set()
        raw_definitions = []
        for ideas_block in find_named_blocks(parsed.root, "ideas"):
            for entry in walk_entries(ideas_block):
                if not isinstance(entry.value, Block):
                    continue
                match = re.match(r"^([A-Z]{3})_[A-Za-z0-9_]+$", entry.key.value)
                if match:
                    tags_in_file.add(match.group(1))
            for group_name in ("country", "hidden_ideas"):
                for group_entry in direct_entries(ideas_block, group_name):
                    if not isinstance(group_entry.value, Block):
                        continue
                    for entry in group_entry.value.entries:
                        if isinstance(entry, Entry) and isinstance(entry.value, Block):
                            raw_definitions.append((entry.key.value, entry.value, group_name, entry.line))

        fallback_tag = None
        if not path.name.startswith("AA_") and len(tags_in_file) == 1:
            fallback_tag = next(iter(tags_in_file))

        for idea_id, block, group_name, line in raw_definitions:
            match = re.match(r"^([A-Z]{3})_", idea_id)
            owner_tag = match.group(1) if match else fallback_tag
            modifier_blocks = direct_entries(block, "modifier")
            custom_tooltips = [
                scalar(item) for item in nested_entries(block, "custom_modifier_tooltip")
                if scalar(item)
            ]
            definitions.append({
                "id": idea_id,
                "owner_tag": owner_tag,
                "group": group_name,
                "visibility": "hidden" if group_name == "hidden_ideas" else "visible",
                "name": get_scalar(block, "name"),
                "picture": get_scalar(block, "picture"),
                "has_modifier": bool(modifier_blocks),
                "modifier_entries": sum(
                    len(item.value.entries) for item in modifier_blocks
                    if isinstance(item.value, Block)
                ),
                "has_on_add": bool(direct_entries(block, "on_add")),
                "has_on_remove": bool(direct_entries(block, "on_remove")),
                "has_cancel": bool(direct_entries(block, "cancel")),
                "has_allowed_civil_war": bool(direct_entries(block, "allowed_civil_war")),
                "days_remove": get_scalar(block, "days_remove"),
                "custom_modifier_tooltips": custom_tooltips,
                "path": str(path),
                "line": line,
            })
        for issue in parsed.issues:
            parse_errors.append("{}:{}: {}".format(path.name, issue.line, issue.message))
    return definitions, parse_errors


def build_content_indexes(repo: Union[str, Path], countries, loc_index):
    """Index country ideas and scripted localisation declared inside this repository."""
    mod = Path(repo) / "mdredux"
    country_tags = set(countries)
    idea_ids = defaultdict(set)
    scripted_defs = defaultdict(list)
    script_parse_errors = defaultdict(list)

    ideas_dir = mod / "common" / "ideas"
    for path in iter_files(ideas_dir, ".txt"):
        parsed = parse_hoi(read(path))
        tags_in_file = set()
        for ideas_block in find_named_blocks(parsed.root, "ideas"):
            for entry in walk_entries(ideas_block):
                if not isinstance(entry.value, Block):
                    continue
                match = re.match(r"^([A-Z]{3})_[A-Za-z0-9_]+$", entry.key.value)
                if match:
                    tag, idea_id = match.group(1), entry.key.value
                    idea_ids[tag].add(idea_id)
                    if tag in country_tags:
                        tags_in_file.add(tag)
        for tag in tags_in_file:
            for issue in parsed.issues:
                script_parse_errors[tag].append("{}:{}".format(path.name, issue))

    script_dir = mod / "common" / "scripted_localisation"
    for path in iter_files(script_dir, ".txt"):
        parsed = parse_hoi(read(path))
        tags_in_file = set()
        for definition in direct_entries(parsed.root, "defined_text"):
            if not isinstance(definition.value, Block):
                continue
            name = get_scalar(definition.value, "name")
            if not name:
                continue
            match = re.match(r"^([A-Z]{3})_[A-Za-z0-9_]+$", name)
            if not match or match.group(1) not in country_tags:
                continue
            tag = match.group(1)
            tags_in_file.add(tag)
            localization_keys = [scalar(e) for e in nested_entries(definition.value, "localization_key")]
            idea_refs = [scalar(e) for e in nested_entries(definition.value, "has_idea")]
            scripted_defs[tag].append({
                "name": name,
                "path": str(path),
                "localization_keys": [value for value in localization_keys if value],
                "idea_refs": [value for value in idea_refs if value],
            })
        # File names such as 99_KAZ_scripted_localisation.txt are useful even if a
        # malformed file contains no parseable defined_text block.
        file_tag = re.match(r"(?:99_)?([A-Z]{3})_", path.name)
        if file_tag and file_tag.group(1) in country_tags:
            tags_in_file.add(file_tag.group(1))
        for tag in tags_in_file:
            for issue in parsed.issues:
                script_parse_errors[tag].append("{}:{}".format(path.name, issue))

    scripted_refs = defaultdict(set)
    script_ref_re = re.compile(r"\[([A-Z]{3}_[A-Za-z0-9_]+)\]")
    for key, occurrences in loc_index.items():
        for occurrence in occurrences:
            for name in script_ref_re.findall(occurrence.value):
                tag = name[:3]
                if tag in country_tags:
                    scripted_refs[tag].add(name)

    idea_definitions, idea_parse_errors = build_idea_definition_index(repo, countries)
    for item in idea_definitions:
        owner_tag = item["owner_tag"]
        if owner_tag:
            idea_ids[owner_tag].add(item["id"])

    return {
        "idea_ids": idea_ids,
        "idea_definitions": idea_definitions,
        "idea_parse_errors": idea_parse_errors,
        "scripted_defs": scripted_defs,
        "scripted_refs": scripted_refs,
        "script_parse_errors": script_parse_errors,
    }



def build_idea_lifecycle_audit(repo, countries, loc_index, content_indexes, event_parsed=None):
    """Audit idea definitions, their grant/removal chain and custom tooltip references."""
    mod = Path(repo) / "mdredux"
    country_tags = set(countries)
    definitions = list(content_indexes.get("idea_definitions", []))
    definitions_by_id = defaultdict(list)
    for item in definitions:
        definitions_by_id[item["id"]].append(item)
    defined_ids = set(definitions_by_id)

    duplicate_idea_ids = [
        {"id": idea_id, "definitions": [
            {"path": item["path"], "line": item["line"], "visibility": item["visibility"]}
            for item in values
        ]}
        for idea_id, values in sorted(definitions_by_id.items()) if len(values) > 1
    ]

    def resolved_name_key(item):
        key = item.get("name") or item["id"]
        seen = {item["id"]}
        while key in definitions_by_id and key not in seen:
            seen.add(key)
            base = definitions_by_id[key][0]
            key = base.get("name") or base["id"]
        return key

    missing_name_localisation = []
    stage_name_links = []
    legacy_ids_without_suffix = []
    for item in definitions:
        if item["owner_tag"] not in country_tags:
            continue
        name_key = resolved_name_key(item)
        if name_key not in loc_index:
            missing_name_localisation.append({
                "idea": item["id"], "name_key": name_key,
                "path": item["path"], "line": item["line"],
            })
        if item.get("name") in defined_ids and item["name"] != item["id"]:
            stage_name_links.append({
                "idea": item["id"], "base_idea": item["name"],
                "path": item["path"], "line": item["line"],
            })
        if not item["id"].endswith("_idea"):
            legacy_ids_without_suffix.append({
                "idea": item["id"], "path": item["path"], "line": item["line"],
            })

    # Inspect common scripts, events and country history; idea definitions themselves
    # are excluded so their metadata is not mistaken for grant/read/remove effects.
    sources = []
    common_dir = mod / "common"
    ideas_dir = common_dir / "ideas"
    for path in iter_files(common_dir, ".txt"):
        if ideas_dir in path.parents:
            continue
        sources.append((path, parse_hoi(read(path))))
    for path, parsed in (event_parsed or {}).items():
        sources.append((Path(path), parsed))
    history_dirs = (mod / "history" / "countries", common_dir / "history" / "countries")
    history_files = sorted({
        path for directory in history_dirs for path in iter_files(directory, ".txt")
    })
    # Match state-flow discovery for extensionless scripted files. The broad
    # .txt scan above already covers normal script files; only add unseen paths.
    existing_source_paths = {path for path, _ in sources}
    for directory in (
        common_dir / "scripted_effects",
        common_dir / "scripted_triggers",
        common_dir / "on_actions",
    ):
        for path in _state_flow_script_files(directory):
            if path not in existing_source_paths:
                sources.append((path, parse_hoi(read(path))))
                existing_source_paths.add(path)

    for path in history_files:
        if path not in existing_source_paths:
            sources.append((path, parse_hoi(read(path))))
            existing_source_paths.add(path)

    references = []
    granted_ids = set()
    source_parse_errors = []

    def values_from(entry):
        if isinstance(entry.value, Token):
            return [entry.value.value]
        if not isinstance(entry.value, Block):
            return []
        values = []
        for child in entry.value.items:
            if isinstance(child, Token):
                values.append(child.value)
            elif isinstance(child, Entry) and child.key.value in ("idea", "add_idea", "remove_idea"):
                value = scalar(child)
                if value:
                    values.append(value)
        return values

    def add_ref(idea_id, usage, path, line):
        if not idea_id or idea_id.lower() in ("no", "none", "empty"):
            return
        references.append({"idea": idea_id, "usage": usage, "path": str(path), "line": line})
        if usage in ("add", "timed_add"):
            granted_ids.add(idea_id)

    for path, parsed in sources:
        for issue in parsed.issues:
            source_parse_errors.append("{}:{}: {}".format(path, issue.line, issue.message))
        for entry in walk_entries(parsed.root):
            key = entry.key.value
            if key in ("add_ideas", "add_idea"):
                for idea_id in values_from(entry):
                    add_ref(idea_id, "add", path, entry.line)
            elif key in ("remove_ideas", "remove_idea"):
                for idea_id in values_from(entry):
                    add_ref(idea_id, "remove", path, entry.line)
            elif key in ("has_idea", "has_ideas"):
                for idea_id in values_from(entry):
                    add_ref(idea_id, "condition", path, entry.line)
            elif key == "add_timed_idea" and isinstance(entry.value, Block):
                add_ref(get_scalar(entry.value, "idea"), "timed_add", path, entry.line)

    missing_local_references = []
    external_references = []
    unresolved_unprefixed_references = []
    for item in references:
        if item["idea"] in defined_ids:
            continue
        match = re.match(r"^([A-Z]{3})_", item["idea"])
        if match and match.group(1) in country_tags:
            missing_local_references.append(dict(item))
        elif match:
            external_references.append(dict(item))
        else:
            unresolved_unprefixed_references.append(dict(item))

    scripted_names = {
        item["name"]
        for definitions_for_tag in content_indexes.get("scripted_defs", {}).values()
        for item in definitions_for_tag
    }
    tooltip_missing_loc = []
    tooltip_scripted_candidates = []
    tooltip_static_key_candidates = []
    for item in definitions:
        if item["owner_tag"] not in country_tags:
            continue
        for tooltip_key in item["custom_modifier_tooltips"]:
            if tooltip_key not in loc_index:
                tooltip_missing_loc.append({
                    "idea": item["id"], "tooltip_key": tooltip_key,
                    "path": item["path"], "line": item["line"],
                })
                continue
            value = get_loc_value(loc_index, tooltip_key) or ""
            bracket_refs = re.findall(r"\[([A-Za-z_][A-Za-z0-9_]*)\]", value)
            if bracket_refs:
                tooltip_scripted_candidates.append({
                    "idea": item["id"], "tooltip_key": tooltip_key,
                    "bracket_references": bracket_refs,
                    "defined_text_names_found": [
                        name for name in bracket_refs if name in scripted_names
                    ],
                    "path": item["path"], "line": item["line"],
                })
            for nested_key in re.findall(r"\$([A-Za-z0-9_.-]+)\$", value):
                if nested_key.startswith(item["owner_tag"] + "_") and nested_key not in loc_index:
                    tooltip_static_key_candidates.append({
                        "idea": item["id"], "tooltip_key": tooltip_key,
                        "nested_localisation_key": nested_key,
                        "path": item["path"], "line": item["line"],
                    })

    scripted_idea_refs = {
        idea_id
        for definitions_for_tag in content_indexes.get("scripted_defs", {}).values()
        for definition in definitions_for_tag
        for idea_id in definition.get("idea_refs", [])
    }
    hidden_ids = {item["id"] for item in definitions if item["visibility"] == "hidden"}
    hidden_with_scripted_refs = hidden_ids & scripted_idea_refs

    locally_ungranted = [
        {
            "idea": item["id"], "path": item["path"], "line": item["line"],
            "visibility": item["visibility"], "owner_tag": item["owner_tag"],
        }
        for item in definitions
        if item["owner_tag"] in country_tags and item["id"] not in granted_ids
    ]
    locally_ungranted.sort(key=lambda item: (item["owner_tag"], item["idea"]))

    return {
        "counts": {
            "idea_files": len(iter_files(ideas_dir, ".txt")),
            "definitions": len(definitions),
            "visible_ideas": sum(1 for item in definitions if item["visibility"] == "visible"),
            "hidden_ideas": len(hidden_ids),
            "idea_references": len(references),
            "add_references": sum(1 for item in references if item["usage"] == "add"),
            "timed_add_references": sum(1 for item in references if item["usage"] == "timed_add"),
            "remove_references": sum(1 for item in references if item["usage"] == "remove"),
            "condition_references": sum(1 for item in references if item["usage"] == "condition"),
            "ideas_with_on_add": sum(1 for item in definitions if item["has_on_add"]),
            "ideas_with_on_remove": sum(1 for item in definitions if item["has_on_remove"]),
            "ideas_with_cancel": sum(1 for item in definitions if item["has_cancel"]),
            "ideas_with_allowed_civil_war": sum(1 for item in definitions if item["has_allowed_civil_war"]),
            "custom_modifier_tooltips": sum(len(item["custom_modifier_tooltips"]) for item in definitions),
            "history_files": len(history_files),
        },
        "parse_errors": list(content_indexes.get("idea_parse_errors", [])),
        "source_parse_errors": source_parse_errors,
        "duplicate_idea_ids": duplicate_idea_ids,
        "missing_name_localisation": missing_name_localisation,
        "stage_name_links": stage_name_links,
        "legacy_ids_without_idea_suffix": legacy_ids_without_suffix,
        "missing_local_idea_references": missing_local_references,
        "external_idea_references": external_references,
        "unresolved_unprefixed_idea_references": unresolved_unprefixed_references,
        "not_locally_granted_candidates": locally_ungranted[:100],
        "not_locally_granted_candidates_truncated": max(0, len(locally_ungranted) - 100),
        "custom_modifier_tooltip_missing_localisation": tooltip_missing_loc,
        "custom_modifier_tooltip_scripted_loc_candidates": tooltip_scripted_candidates,
        "custom_modifier_tooltip_static_key_candidates": tooltip_static_key_candidates,
        "hidden_ideas_with_scripted_loc_refs": len(hidden_with_scripted_refs),
        "hidden_ideas_without_scripted_loc_refs": len(hidden_ids - hidden_with_scripted_refs),
        "history_inventory_available": bool(history_files),
        "idea_definitions": definitions,
        "idea_references": references,
    }



def build_global_indexes(countries, repo=None):
    """Index focus IDs and every event file in the available mod slice."""
    all_focus = set()
    defined_events = set()
    defined_namespaces = set()
    event_parsed = {}
    for country in countries.values():
        parsed = country["tree_parsed"]
        for body in find_named_blocks(parsed.root, "focus"):
            fid = get_scalar(body, "id")
            if fid:
                all_focus.add(fid)

    event_paths = set()
    if repo is not None:
        event_paths.update(iter_files(Path(repo) / "mdredux" / "events", ".txt"))
    else:
        event_paths.update(country["events"] for country in countries.values() if country["events"])

    for event_path in sorted(event_paths, key=lambda path: str(path)):
        ep = parse_hoi(read(event_path))
        event_parsed[event_path] = ep
        for entry in direct_entries(ep.root, "add_namespace"):
            ns = scalar(entry)
            if ns:
                defined_namespaces.add(ns)
        for kind in ("country_event", "news_event"):
            for event_entry in direct_entries(ep.root, kind):
                if isinstance(event_entry.value, Block):
                    event_id = get_scalar(event_entry.value, "id")
                    if event_id:
                        defined_events.add(event_id)
    return all_focus, defined_events, defined_namespaces, event_parsed


def get_loc_value(loc_index: Dict[str, List[LocEntry]], key: str) -> Optional[str]:
    entries = loc_index.get(key, [])
    return entries[0].value if entries else None


def focus_prerequisite_ids(focus_block: Block) -> List[str]:
    found = []
    for prerequisite in direct_entries(focus_block, "prerequisite"):
        if isinstance(prerequisite.value, Block):
            for entry in nested_entries(prerequisite.value, "focus"):
                value = scalar(entry)
                if value:
                    found.append(value)
    return found


def has_disabled_allow_branch(focus_block: Block) -> bool:
    for branch in find_named_blocks(focus_block, "allow_branch"):
        if get_scalar(branch, "always") == "no":
            return True
    return False


def idea_candidates(block: Block) -> Iterator[str]:
    """Yield idea IDs referenced by common HOI4 idea effects/triggers in a block."""
    idea_commands = {"add_ideas", "add_idea", "remove_idea", "remove_ideas", "has_idea", "has_ideas", "idea"}
    for entry in walk_entries(block):
        if entry.key.value not in idea_commands:
            continue
        if isinstance(entry.value, Token):
            yield entry.value.value
        else:
            for item in entry.value.items:
                if isinstance(item, Token):
                    yield item.value
                elif isinstance(item, Entry) and item.key.value in idea_commands and isinstance(item.value, Token):
                    yield item.value.value



EVENT_CALL_KEYS = frozenset(("country_event", "news_event"))


def iter_event_calls(block: Block):
    """Yield real event calls in both scalar and block syntax; skip display-only tooltips."""
    def visit(current: Block):
        for item in current.items:
            if not isinstance(item, Entry):
                continue
            if item.key.value in EVENT_CALL_KEYS:
                event_id = item.value.value if isinstance(item.value, Token) else get_scalar(item.value, "id")
                if event_id:
                    yield item.key.value, event_id, item.line
            if isinstance(item.value, Block) and item.key.value != "effect_tooltip":
                yield from visit(item.value)

    yield from visit(block)


def is_local_event_key(key: str, event_id: str, tag: Optional[str] = None) -> bool:
    """Recognize event-local keys without treating shared/base keys as local."""
    namespace = event_id.split(".", 1)[0] if "." in event_id else ""
    if namespace and (key == namespace or key.startswith(namespace + ".") or key.startswith(namespace + "_")):
        return True
    return bool(tag and key.startswith(tag + "_"))


def build_event_audit(repo, countries, loc_index, event_parsed, content_indexes=None):
    """Build project-wide event, localisation, reference and chain diagnostics."""
    mod = Path(repo) / "mdredux"
    file_tags = {
        str(country["events"]): tag
        for tag, country in countries.items()
        if country["events"] is not None
    }
    definitions = []
    namespace_declarations = []
    parse_errors = []
    missing_event_ids = []
    missing_title_fields = []
    missing_desc_fields = []
    missing_option_names = []

    for path, parsed in event_parsed.items():
        for issue in parsed.issues:
            parse_errors.append("{}:{}".format(path, issue))
        for entry in direct_entries(parsed.root, "add_namespace"):
            ns = scalar(entry)
            if ns:
                namespace_declarations.append({"namespace": ns, "path": str(path), "line": entry.line})
        for kind in ("country_event", "news_event"):
            for event_entry in direct_entries(parsed.root, kind):
                if not isinstance(event_entry.value, Block):
                    continue
                body = event_entry.value
                id_entry = next((item for item in direct_entries(body, "id") if scalar(item)), None)
                event_id = scalar(id_entry) if id_entry else None
                if not event_id:
                    missing_event_ids.append({"kind": kind, "path": str(path), "line": event_entry.line})
                    continue
                trigger = get_block(body, "trigger")
                trigger_tags = [scalar(item) for item in nested_entries(trigger, "tag")] if trigger else []
                trigger_tags = [value for value in trigger_tags if value]
                trigger_scopes = sorted({
                    item.key.value for item in walk_entries(trigger)
                    if isinstance(item.value, Block) and item.key.value.upper() in ("FROM", "ROOT", "PREV", "THIS")
                }) if trigger else []
                title = get_scalar(body, "title")
                desc = get_scalar(body, "desc")
                if not title:
                    missing_title_fields.append({"id": event_id, "kind": kind, "path": str(path), "line": id_entry.line})
                if not desc:
                    missing_desc_fields.append({"id": event_id, "kind": kind, "path": str(path), "line": id_entry.line})
                definitions.append({
                    "id": event_id, "kind": kind, "path": str(path), "line": id_entry.line,
                    "block": body, "title": title, "desc": desc,
                    "picture": get_scalar(body, "picture"),
                    "is_triggered_only": (get_scalar(body, "is_triggered_only") or "").lower() in ("yes", "true", "1"),
                    "fire_only_once": (get_scalar(body, "fire_only_once") or "").lower() in ("yes", "true", "1"),
                    "has_trigger": trigger is not None,
                    "trigger_tags": trigger_tags, "trigger_scopes": trigger_scopes,
                    "option_count": len(direct_entries(body, "option")),
                })

    definitions_by_id = defaultdict(list)
    for definition in definitions:
        definitions_by_id[definition["id"]].append(definition)
    duplicate_event_ids = []
    for event_id, occurrences in sorted(definitions_by_id.items()):
        if len(occurrences) > 1:
            duplicate_event_ids.append({
                "id": event_id,
                "definitions": [
                    {"kind": item["kind"], "path": item["path"], "line": item["line"]}
                    for item in occurrences
                ],
            })

    namespace_groups = defaultdict(list)
    for item in namespace_declarations:
        namespace_groups[item["namespace"]].append(item)
    duplicate_namespaces = []
    for namespace, occurrences in sorted(namespace_groups.items()):
        if len(occurrences) > 1:
            same_file = len({item["path"] for item in occurrences}) == 1
            duplicate_namespaces.append({
                "namespace": namespace, "scope": "same_file" if same_file else "multiple_files",
                "declarations": occurrences,
            })

    reused_loc = defaultdict(list)
    missing_loc, external_loc = [], []
    missing_option_loc, external_option_loc = [], []
    duplicate_loc_definitions = []
    generic_option_labels, long_option_labels = [], []
    option_loc_lines = []
    missing_event_idea_candidates = []
    missing_event_scripted_loc = []
    idea_index = (content_indexes or {}).get("idea_ids", {})
    scripted_definitions = (content_indexes or {}).get("scripted_defs", {})
    scripted_names = {
        tag: {item["name"] for item in items}
        for tag, items in scripted_definitions.items()
    }
    scripted_ref_re = re.compile(r"\[([A-Z]{3}_[A-Za-z0-9_]+)\]")
    for definition in definitions:
        tag = file_tags.get(definition["path"])
        for field in ("title", "desc"):
            key = definition[field]
            if not key:
                continue
            reused_loc[(field, key)].append({
                "event_id": definition["id"], "path": definition["path"], "line": definition["line"],
            })
            if key not in loc_index:
                item = {"field": field, "key": key, "event_id": definition["id"],
                        "path": definition["path"], "line": definition["line"]}
                (missing_loc if is_local_event_key(key, definition["id"], tag) else external_loc).append(item)
            elif len(loc_index[key]) > 1:
                duplicate_loc_definitions.append({
                    "field": field, "key": key,
                    "definitions": [{"path": loc.path, "line": loc.line} for loc in loc_index[key]],
                })

        for option_entry in direct_entries(definition["block"], "option"):
            if not isinstance(option_entry.value, Block):
                continue
            option = option_entry.value
            key = get_scalar(option, "name")
            if not key:
                missing_option_names.append({
                    "event_id": definition["id"], "path": definition["path"], "line": option_entry.line,
                })
            elif key not in loc_index:
                item = {"key": key, "event_id": definition["id"],
                        "path": definition["path"], "line": option_entry.line}
                (missing_option_loc if is_local_event_key(key, definition["id"], tag) else external_option_loc).append(item)
            else:
                label = get_loc_value(loc_index, key)
                if label:
                    label_info = {
                        "key": key, "label": label, "event_id": definition["id"],
                        "path": definition["path"], "line": option_entry.line,
                    }
                    if label.strip().rstrip(".!?").lower() in GENERIC_LABELS:
                        generic_option_labels.append(label_info)
                    elif len(label) > 35:
                        long_option_labels.append(label_info)
            # Check log independently: a missing name must not hide a missing log.
            if get_scalar(option, "log") is None:
                option_loc_lines.append({
                    "key": key or "?", "event_id": definition["id"],
                    "path": definition["path"], "line": option_entry.line,
                })

    # Event-local idea references are compared against this repository slice.
    # Missing IDs are candidates: cross-country and base-MD ideas may be external.
    for definition in definitions:
        source_tag = file_tags.get(definition["path"])
        for idea_id in idea_candidates(definition["block"]):
            match = re.match(r"^([A-Z]{3})_[A-Za-z0-9_]+$", idea_id)
            if not match:
                continue
            tag = match.group(1)
            if tag in countries and idea_id not in idea_index.get(tag, set()):
                missing_event_idea_candidates.append({
                    "event_id": definition["id"], "idea": idea_id, "tag": tag,
                    "classification": "local_candidate" if source_tag == tag else "external_or_cross_country_candidate",
                    "path": definition["path"], "line": definition["line"],
                })

        localisation_keys = [definition["title"], definition["desc"]]
        for option_entry in direct_entries(definition["block"], "option"):
            if isinstance(option_entry.value, Block):
                option_name = get_scalar(option_entry.value, "name")
                if option_name:
                    localisation_keys.append(option_name)
        for loc_key in filter(None, localisation_keys):
            for occurrence in loc_index.get(loc_key, []):
                for name in scripted_ref_re.findall(occurrence.value):
                    tag = name[:3]
                    if tag in countries and name not in scripted_names.get(tag, set()):
                        missing_event_scripted_loc.append({
                            "event_id": definition["id"], "localisation_key": loc_key,
                            "scripted_localisation": name, "path": occurrence.path,
                            "line": occurrence.line,
                        })

    reused_event_loc = []
    for (field, key), occurrences in sorted(reused_loc.items()):
        event_ids = sorted({item["event_id"] for item in occurrences})
        if len(event_ids) > 1:
            reused_event_loc.append({"field": field, "key": key, "event_ids": event_ids, "uses": occurrences})

    references = []

    def add_references(block, source_kind, source_path, caller):
        for call_kind, target_id, line in iter_event_calls(block):
            references.append({
                "kind": call_kind, "target": target_id, "source_kind": source_kind,
                "source": str(source_path), "caller": caller, "line": line,
            })

    for tag, country in countries.items():
        for focus in find_named_blocks(country["tree_parsed"].root, "focus"):
            focus_id = get_scalar(focus, "id") or "unknown_focus"
            add_references(focus, "focus", country["tree"], focus_id)

    decisions_dir = mod / "common" / "decisions"
    for path in iter_files(decisions_dir, ".txt"):
        parsed = parse_hoi(read(path))
        add_references(parsed.root, "decision", path, path.stem)

    for folder, source_kind in (("scripted_effects", "scripted_effect"), ("on_actions", "on_action")):
        source_dir = mod / "common" / folder
        # Match state-flow inventory: HOI4 script files may be extensionless.
        for path in _state_flow_script_files(source_dir):
            parsed = event_parsed.get(path)
            if parsed is None:
                parsed = parse_hoi(read(path))
                for issue in parsed.issues:
                    parse_errors.append("{}:{}".format(path, issue))
            add_references(parsed.root, source_kind, path, path.stem)

    # Country history can schedule events at start dates; treat these as graph roots.
    history_dirs = (mod / "history" / "countries", mod / "common" / "history" / "countries")
    history_files = sorted({
        path for directory in history_dirs for path in iter_files(directory, ".txt")
    })
    for path in history_files:
        parsed = parse_hoi(read(path))
        for issue in parsed.issues:
            parse_errors.append("{}:{}".format(path, issue))
        add_references(parsed.root, "history", path, path.stem)

    for definition in definitions:
        add_references(definition["block"], "event", definition["path"], definition["id"])

    defined_ids = set(definitions_by_id)
    defined_namespaces = {item["namespace"] for item in namespace_declarations}
    unresolved_references, external_references = [], []
    event_edges = defaultdict(set)
    root_events = set()
    scripted_effect_references = []
    scripted_effect_targets = set()
    for reference in references:
        target = reference["target"]
        if target in defined_ids:
            if reference["source_kind"] == "event":
                event_edges[reference["caller"]].add(target)
            elif reference["source_kind"] == "scripted_effect":
                # A definition can contain a call without ever being invoked itself.
                # Keep the reference visible but do not treat it as proof of reachability.
                scripted_effect_references.append(dict(reference))
                scripted_effect_targets.add(target)
            else:
                root_events.add(target)
            continue
        namespace = target.split(".", 1)[0] if "." in target else ""
        (unresolved_references if namespace and namespace in defined_namespaces else external_references).append(dict(reference))

    reachable = set()
    pending = list(root_events)
    while pending:
        current = pending.pop()
        if current in reachable:
            continue
        reachable.add(current)
        pending.extend(event_edges.get(current, ()))

    orphan_triggered = []
    for definition in definitions:
        if (definition["is_triggered_only"] and definition["id"] not in reachable
                and definition["id"] not in scripted_effect_targets):
            orphan_triggered.append({
                "id": definition["id"], "kind": definition["kind"], "path": definition["path"],
                "line": definition["line"], "has_trigger": definition["has_trigger"],
                "fire_only_once": definition["fire_only_once"],
            })

    missing_picture = [
        {"id": item["id"], "kind": item["kind"], "path": item["path"], "line": item["line"]}
        for item in definitions if not item["picture"]
    ]
    metadata = [{key: value for key, value in item.items() if key != "block"} for item in definitions]
    kind_counts = Counter(item["kind"] for item in definitions)

    return {
        "counts": {"definitions": len(definitions), "country_event": kind_counts.get("country_event", 0),
                   "news_event": kind_counts.get("news_event", 0), "namespaces": len(namespace_groups)},
        "parse_errors": parse_errors, "missing_event_ids": missing_event_ids,
        "missing_title_fields": missing_title_fields, "missing_desc_fields": missing_desc_fields,
        "missing_option_names": missing_option_names,
        "duplicate_event_ids": duplicate_event_ids, "duplicate_namespaces": duplicate_namespaces,
        "missing_localisation": missing_loc, "external_localisation": external_loc,
        "duplicate_localisation_definitions": duplicate_loc_definitions,
        "missing_option_localisation": missing_option_loc, "external_option_localisation": external_option_loc,
        "generic_option_labels": generic_option_labels, "long_option_labels": long_option_labels,
        "options_without_log": option_loc_lines,
        "missing_event_idea_candidates": missing_event_idea_candidates,
        "missing_event_scripted_localisation": missing_event_scripted_loc,
        "reused_title_desc_keys": reused_event_loc, "unresolved_references": unresolved_references,
        "external_references": external_references, "scripted_effect_references": scripted_effect_references,
        "unreachable_triggered_events": orphan_triggered,
        "events_without_picture": missing_picture, "metadata": metadata,
        "references": references,
        "event_edges": [dict(item) for item in references
                        if item["source_kind"] == "event" and item["target"] in defined_ids],
        "root_events": sorted(root_events), "reachable_events": sorted(reachable),
    }



DECISION_CATEGORY_FIELDS = frozenset({
    "allowed", "visible", "potential", "priority", "icon", "picture", "name", "desc",
    "visible_when_empty", "collapse", "scripted_gui", "on_map_mode", "background", "decision_icon",
})
DECISION_REF_KEYS = frozenset({"has_decision", "has_completed_decision", "has_taken_decision", "has_activated_decision"})
FLAG_READ_KEYS = frozenset({"has_country_flag", "has_global_flag"})
FLAG_WRITE_KEYS = frozenset({"set_country_flag", "clr_country_flag", "set_global_flag", "clr_global_flag"})

STATE_FLOW_FLAG_READ_KEYS = frozenset({
    "has_country_flag", "has_global_flag", "has_state_flag", "has_province_flag",
})
STATE_FLOW_FLAG_WRITE_KEYS = frozenset({
    "set_country_flag", "clr_country_flag", "set_global_flag", "clr_global_flag",
    "set_state_flag", "clr_state_flag", "set_province_flag", "clr_province_flag",
    "set_timed_country_flag", "set_timed_global_flag",
    "set_timed_state_flag", "set_timed_province_flag",
})
STATE_FLOW_VARIABLE_WRITE_KEYS = frozenset({
    "set_variable", "set_temp_variable", "add_to_variable", "subtract_from_variable",
    "multiply_variable", "divide_variable", "clamp_variable", "modulo_variable",
})
STATE_FLOW_VARIABLE_READ_KEYS = frozenset({"check_variable", "compare_variables"})
STATE_FLOW_ARRAY_WRITE_KEYS = frozenset({"add_to_array", "remove_from_array", "clear_array"})
STATE_FLOW_ARRAY_READ_KEYS = frozenset({
    "any_of_scopes", "all_of_scopes", "random_scope_in_array", "for_each_scope_loop",
})
STATE_FLOW_FLAG_SCOPE = {
    "set_country_flag": "country", "clr_country_flag": "country",
    "set_global_flag": "global", "clr_global_flag": "global",
    "set_state_flag": "state", "clr_state_flag": "state",
    "set_province_flag": "province", "clr_province_flag": "province",
    "set_timed_country_flag": "country_timed", "set_timed_global_flag": "global_timed",
    "set_timed_state_flag": "state_timed", "set_timed_province_flag": "province_timed",
}
STATE_FLOW_FLAG_READ_SCOPE = {
    "has_country_flag": "country", "has_global_flag": "global",
    "has_state_flag": "state", "has_province_flag": "province",
}
STATE_FLOW_IDEA_READ_KEYS = frozenset({"has_idea", "has_ideas"})
STATE_FLOW_IDEA_WRITE_KEYS = frozenset({"add_ideas", "add_idea", "add_timed_idea"})
STATE_FLOW_VARIABLE_META_KEYS = frozenset({
    "var", "variable", "value", "value_add", "days", "operation", "type",
    "round", "abs", "clamp", "min", "max",
})
STATE_FLOW_ARRAY_META_KEYS = frozenset({
    "array", "source_array", "target_array", "value", "amount", "count",
    "index", "position", "scope",
})


def decision_owner_tag(path: Path, countries) -> Optional[str]:
    stem = path.stem.lower()
    for tag, country in countries.items():
        tree_name = country["tree"].name
        suffix = "_Focus_Tree.txt"
        tree_stem = tree_name[:-len(suffix)] if tree_name.endswith(suffix) else Path(tree_name).stem
        if tree_stem.lower() == stem:
            return tag
    return None


def decision_reference_value(entry: Entry) -> Optional[str]:
    if isinstance(entry.value, Token):
        return entry.value.value
    for key in ("decision", "id", "name", "flag"):
        value = get_scalar(entry.value, key)
        if value:
            return value
    return None


def iter_named_script_refs(block: Block, commands) -> Iterator[str]:
    for entry in walk_entries(block):
        if entry.key.value in commands:
            value = decision_reference_value(entry)
            if value:
                yield value


def decision_tooltip_keys(block: Block) -> List[str]:
    found = []
    for entry in walk_entries(block):
        key = entry.key.value
        if key == "custom_cost_text":
            value = scalar(entry)
            if value:
                found.append(value)
        elif key == "custom_effect_tooltip":
            value = scalar(entry)
            if value:
                found.append(value)
            elif isinstance(entry.value, Block):
                for nested in walk_entries(entry.value):
                    if nested.key.value in ("localization_key", "tooltip") and scalar(nested):
                        found.append(scalar(nested))
        elif key == "custom_trigger_tooltip" and isinstance(entry.value, Block):
            for nested in walk_entries(entry.value):
                if nested.key.value in ("tooltip", "localization_key") and scalar(nested):
                    found.append(scalar(nested))
    return found


def numeric_value(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


PARSE_ERROR_FIELDS = (
    "parse_errors", "source_parse_errors", "mio_parse_errors",
    "equipment_parse_errors", "module_parse_errors", "technology_parse_errors",
    "script_parse_errors",
)


def reports_have_parse_errors(*reports) -> bool:
    """Return True if any report contains a parser failure from any audit subsystem."""
    return any(bool(report.get(field)) for report in reports for field in PARSE_ERROR_FIELDS)


def has_obvious_manual_cost_debit(effect_blocks: Sequence[Optional[Block]]) -> bool:
    entries = []
    for block in effect_blocks:
        if block is not None:
            entries.extend(list(walk_entries(block)))
    for entry in entries:
        if entry.key.value in ("subtract_from_variable", "subtract_from_array"):
            return True
        if entry.key.value in ("add_political_power", "add_command_power", "add_army_experience",
                               "add_navy_experience", "add_air_experience"):
            value = numeric_value(scalar(entry))
            if value is not None and value < 0:
                return True
        if entry.key.value in ("add_to_variable", "add_to_array", "add_equipment_to_stockpile", "add_resource"):
            if isinstance(entry.value, Block):
                amount_entries = direct_entries(entry.value, "amount") + direct_entries(entry.value, "value")
                if any((numeric_value(scalar(item)) or 0) < 0 for item in amount_entries):
                    return True
    has_treasury_modifier = any(entry.key.value == "modify_treasury_effect" for entry in entries)
    if has_treasury_modifier:
        for entry in entries:
            if entry.key.value == "set_temp_variable" and isinstance(entry.value, Block):
                for variable in entry.value.entries:
                    if variable.key.value == "treasury_change":
                        value = numeric_value(scalar(variable))
                        if value is not None and value < 0:
                            return True
    return False


def collect_state_inventory(mod: Path):
    state_dirs = (mod / "history" / "states", mod / "common" / "history" / "states")
    files = []
    for directory in state_dirs:
        files.extend(iter_files(directory, ".txt"))
    state_ids = set()
    for path in sorted(set(files)):
        parsed = parse_hoi(read(path))
        blocks = find_named_blocks(parsed.root, "state") or [parsed.root]
        for block in blocks:
            for entry in direct_entries(block, "id"):
                value = scalar(entry)
                if value and value.isdigit():
                    state_ids.add(int(value))
    return bool(files), state_ids


def build_decision_audit(repo, countries, loc_index, all_focus, defined_events,
                         defined_namespaces, event_parsed, content_indexes):
    mod = Path(repo) / "mdredux"
    decision_files = iter_files(mod / "common" / "decisions", ".txt")
    categories, decisions, parsed_by_path, parse_errors = [], [], {}, []

    for path in decision_files:
        parsed = parse_hoi(read(path))
        parsed_by_path[path] = parsed
        for issue in parsed.issues:
            parse_errors.append("{}:{}".format(path, issue))
        owner_tag = decision_owner_tag(path, countries)
        for category_entry in parsed.root.entries:
            if not isinstance(category_entry, Entry) or not isinstance(category_entry.value, Block):
                continue
            category_id = category_entry.key.value
            category_block = category_entry.value
            categories.append({
                "id": category_id, "path": str(path), "line": category_entry.line,
                "block": category_block, "owner_tag": owner_tag,
                "has_allowed": bool(direct_entries(category_block, "allowed")),
                "has_visible": bool(direct_entries(category_block, "visible")),
                "has_priority": bool(direct_entries(category_block, "priority")),
            })
            for decision_entry in category_block.entries:
                if not isinstance(decision_entry.value, Block) or decision_entry.key.value in DECISION_CATEGORY_FIELDS:
                    continue
                block = decision_entry.value
                decisions.append({
                    "id": decision_entry.key.value, "category": category_id,
                    "path": str(path), "line": decision_entry.line, "block": block,
                    "owner_tag": owner_tag, "cost": get_scalar(block, "cost"),
                    "days_remove": get_scalar(block, "days_remove"),
                    "days_re_enable": get_scalar(block, "days_re_enable"),
                    "fire_only_once": (get_scalar(block, "fire_only_once") or "").lower() in ("yes", "true", "1"),
                    "has_visible": bool(direct_entries(block, "visible")),
                    "has_available": bool(direct_entries(block, "available")),
                    "has_allowed": bool(direct_entries(block, "allowed")),
                    "has_ai_will_do": bool(direct_entries(block, "ai_will_do")),
                    "has_complete_effect": bool(direct_entries(block, "complete_effect")),
                    "has_remove_effect": bool(direct_entries(block, "remove_effect")),
                    "has_modifier": bool(direct_entries(block, "modifier") or direct_entries(block, "targeted_modifier")),
                    "target_array": get_scalar(block, "target_array"),
                })

    category_groups = defaultdict(list)
    for item in categories:
        category_groups[item["id"]].append(item)
    duplicate_categories = [
        {
            "id": key,
            "scope": "same_file" if len({x["path"] for x in values}) == 1 else "multiple_files",
            "definitions": [{"path": x["path"], "line": x["line"]} for x in values],
        }
        for key, values in sorted(category_groups.items()) if len(values) > 1
    ]

    decision_groups = defaultdict(list)
    for item in decisions:
        decision_groups[item["id"]].append(item)
    duplicate_decisions = [
        {"id": key, "definitions": [
            {"category": x["category"], "path": x["path"], "line": x["line"]} for x in values
        ]}
        for key, values in sorted(decision_groups.items()) if len(values) > 1
    ]
    defined_decisions = set(decision_groups)

    missing_category_loc, missing_decision_loc, duplicate_loc_keys = [], [], []
    missing_tooltip_loc, external_tooltip_loc = [], []
    missing_decision_refs, external_decision_refs = [], []
    missing_focus_refs, external_focus_refs = [], []
    missing_event_refs, external_event_refs = [], []
    idea_reference_candidates, flag_reference_candidates, missing_scripted_loc = [], [], []
    invalid_numeric_fields, custom_cost_pair_issues, custom_cost_conflicts = [], [], []
    custom_cost_without_debit, repeatability_warnings, empty_effect_warnings = [], [], []
    nonnumeric_highlight_states, unknown_highlight_states, highlight_state_refs = [], [], []
    decision_conditions = []

    idea_index = (content_indexes or {}).get("idea_ids", {})
    script_defs = (content_indexes or {}).get("scripted_defs", {})
    script_names = {tag: {item["name"] for item in values} for tag, values in script_defs.items()}
    script_ref_re = re.compile(r"\[([A-Z]{3}_[A-Za-z0-9_]+)\]")

    for category in categories:
        key = category["id"]
        if key not in loc_index:
            missing_category_loc.append({"category": key, "path": category["path"], "line": category["line"]})
        elif len(loc_index[key]) > 1:
            duplicate_loc_keys.append({
                "key": key, "definitions": [{"path": x.path, "line": x.line} for x in loc_index[key]],
            })

    for decision in decisions:
        decision_id, owner_tag, block = decision["id"], decision["owner_tag"], decision["block"]
        if decision_id not in loc_index:
            missing_decision_loc.append({
                "decision": decision_id, "category": decision["category"],
                "path": decision["path"], "line": decision["line"],
            })
        elif len(loc_index[decision_id]) > 1:
            duplicate_loc_keys.append({
                "key": decision_id, "definitions": [{"path": x.path, "line": x.line} for x in loc_index[decision_id]],
            })

        # Decision _desc keys are optional in this TDF slice; duplicate definitions are not.
        desc_key = decision_id + "_desc"
        if len(loc_index.get(desc_key, [])) > 1:
            duplicate_loc_keys.append({
                "key": desc_key, "definitions": [{"path": x.path, "line": x.line} for x in loc_index[desc_key]],
            })

        tooltip_keys = decision_tooltip_keys(block)
        for key in tooltip_keys:
            if key not in loc_index:
                item = {"key": key, "decision": decision_id, "path": decision["path"], "line": decision["line"]}
                (missing_tooltip_loc if owner_tag and key.startswith(owner_tag + "_") else external_tooltip_loc).append(item)
            elif len(loc_index[key]) > 1:
                duplicate_loc_keys.append({
                    "key": key, "definitions": [{"path": x.path, "line": x.line} for x in loc_index[key]],
                })

        keys_to_scan = [decision_id, desc_key, decision["category"], decision["category"] + "_desc"] + tooltip_keys
        for loc_key in keys_to_scan:
            for occurrence in loc_index.get(loc_key, []):
                for name in script_ref_re.findall(occurrence.value):
                    tag = name[:3]
                    if tag in countries and name not in script_names.get(tag, set()):
                        missing_scripted_loc.append({
                            "decision": decision_id, "localisation_key": loc_key,
                            "scripted_localisation": name, "path": occurrence.path, "line": occurrence.line,
                        })

        for entry in walk_entries(block):
            if entry.key.value in DECISION_REF_KEYS:
                target = decision_reference_value(entry)
                if target and target not in defined_decisions:
                    item = {"decision": decision_id, "target": target, "path": decision["path"],
                            "line": entry.line, "field": entry.key.value}
                    (missing_decision_refs if owner_tag and target.startswith(owner_tag + "_") else external_decision_refs).append(item)

            if entry.key.value == "has_completed_focus":
                target = scalar(entry)
                if target and target not in all_focus:
                    item = {"decision": decision_id, "target": target, "path": decision["path"], "line": entry.line}
                    (missing_focus_refs if owner_tag and target.startswith(owner_tag + "_") else external_focus_refs).append(item)

        for _, event_id, line in iter_event_calls(block):
            if event_id not in defined_events:
                namespace = event_id.split(".", 1)[0] if "." in event_id else ""
                item = {"decision": decision_id, "target": event_id, "path": decision["path"], "line": line}
                (missing_event_refs if namespace and namespace in defined_namespaces else external_event_refs).append(item)

        for idea_id in idea_candidates(block):
            match = re.match(r"^([A-Z]{3})_[A-Za-z0-9_]+$", idea_id)
            if match:
                tag = match.group(1)
                if tag in countries and idea_id not in idea_index.get(tag, set()):
                    idea_reference_candidates.append({
                        "decision": decision_id, "idea": idea_id, "owner_tag": owner_tag,
                        "classification": "local_candidate" if tag == owner_tag else "cross_country_candidate",
                        "path": decision["path"], "line": decision["line"],
                    })

        for flag in sorted(set(iter_named_script_refs(block, FLAG_READ_KEYS))):
            if owner_tag and flag.startswith(owner_tag + "_"):
                flag_reference_candidates.append({
                    "decision": decision_id, "flag": flag, "classification": "local_candidate",
                    "path": decision["path"], "line": decision["line"],
                })

        for field in ("cost", "days_remove", "days_re_enable"):
            value = decision[field]
            if value is not None:
                number = numeric_value(value)
                invalid = number is None or (number < 0 and not (field == "days_remove" and number == -1))
                if invalid:
                    invalid_numeric_fields.append({
                        "decision": decision_id, "field": field, "value": value,
                        "path": decision["path"], "line": decision["line"],
                    })

        has_custom_trigger = bool(direct_entries(block, "custom_cost_trigger"))
        custom_text = get_scalar(block, "custom_cost_text")
        if has_custom_trigger != bool(custom_text):
            custom_cost_pair_issues.append({
                "decision": decision_id, "has_custom_cost_trigger": has_custom_trigger,
                "custom_cost_text": custom_text, "path": decision["path"], "line": decision["line"],
            })
        if has_custom_trigger and decision["cost"] is not None:
            custom_cost_conflicts.append({"decision": decision_id, "path": decision["path"], "line": decision["line"]})
        if has_custom_trigger:
            effects = []
            effects.extend([x.value for x in direct_entries(block, "complete_effect") if isinstance(x.value, Block)])
            effects.extend([x.value for x in direct_entries(block, "remove_effect") if isinstance(x.value, Block)])
            if not has_obvious_manual_cost_debit(effects):
                custom_cost_without_debit.append({
                    "decision": decision_id, "custom_cost_text": custom_text,
                    "path": decision["path"], "line": decision["line"],
                })

        cooldown = numeric_value(decision["days_re_enable"])
        if decision["fire_only_once"] and cooldown is not None and cooldown > 0:
            repeatability_warnings.append({
                "decision": decision_id, "reason": "fire_only_once вместе с days_re_enable",
                "days_re_enable": decision["days_re_enable"], "path": decision["path"], "line": decision["line"],
            })

        for field in ("complete_effect", "remove_effect"):
            for entry in direct_entries(block, field):
                if isinstance(entry.value, Block) and not entry.value.entries:
                    empty_effect_warnings.append({
                        "decision": decision_id, "effect": field, "path": decision["path"], "line": entry.line,
                    })

        for field in ("allowed", "visible", "available"):
            condition = get_block(block, field)
            if condition and get_scalar(condition, "always") == "no":
                decision_conditions.append({
                    "decision": decision_id, "condition": field,
                    "reason": "always = no делает условие постоянно ложным; проверь, что это намеренно",
                    "path": decision["path"], "line": decision["line"],
                })

        highlight = get_block(block, "highlight_states")
        if highlight:
            for entry in nested_entries(highlight, "state"):
                value = scalar(entry)
                item = {"decision": decision_id, "state": value, "path": decision["path"], "line": entry.line}
                if value is None or not value.isdigit():
                    nonnumeric_highlight_states.append(item)
                else:
                    highlight_state_refs.append({**item, "state": int(value)})

    flag_setters = set()
    sources = [x["tree_parsed"].root for x in countries.values()]
    sources.extend(x.root for x in event_parsed.values())
    sources.extend(x.root for x in parsed_by_path.values())
    for folder in ("scripted_effects", "on_actions"):
        for path in iter_files(mod / "common" / folder, ".txt"):
            sources.append(parse_hoi(read(path)).root)
    for path in iter_files(mod / "common" / "history" / "countries", ".txt"):
        sources.append(parse_hoi(read(path)).root)
    for source in sources:
        flag_setters.update(iter_named_script_refs(source, FLAG_WRITE_KEYS))
    for item in flag_reference_candidates:
        item["status"] = "setter_found_in_checkout" if item["flag"] in flag_setters else "setter_not_found_in_checkout"

    state_inventory_available, state_ids = collect_state_inventory(mod)
    if state_inventory_available:
        for item in highlight_state_refs:
            if item["state"] not in state_ids:
                unknown_highlight_states.append(item)

    metadata = [{key: value for key, value in item.items() if key != "block"} for item in decisions]
    return {
        "counts": {"files": len(decision_files), "categories": len(categories), "decisions": len(decisions)},
        "parse_errors": parse_errors, "duplicate_category_ids": duplicate_categories,
        "duplicate_decision_ids": duplicate_decisions, "missing_category_localisation": missing_category_loc,
        "missing_decision_localisation": missing_decision_loc, "duplicate_localisation_definitions": duplicate_loc_keys,
        "missing_tooltip_localisation": missing_tooltip_loc, "external_tooltip_localisation": external_tooltip_loc,
        "missing_decision_references": missing_decision_refs, "external_decision_references": external_decision_refs,
        "missing_focus_references": missing_focus_refs, "external_focus_references": external_focus_refs,
        "missing_event_references": missing_event_refs, "external_event_references": external_event_refs,
        "idea_reference_candidates": idea_reference_candidates, "flag_reference_candidates": flag_reference_candidates,
        "missing_scripted_localisation": missing_scripted_loc, "invalid_numeric_fields": invalid_numeric_fields,
        "custom_cost_pair_issues": custom_cost_pair_issues, "custom_cost_conflicts": custom_cost_conflicts,
        "custom_cost_without_debit": custom_cost_without_debit, "repeatability_warnings": repeatability_warnings,
        "empty_effect_warnings": empty_effect_warnings, "condition_review_candidates": decision_conditions,
        "nonnumeric_highlight_states": nonnumeric_highlight_states, "unknown_highlight_states": unknown_highlight_states,
        "highlight_state_references": highlight_state_refs, "state_inventory_available": state_inventory_available,
        "state_inventory_count": len(state_ids), "metadata": metadata,
    }




def build_industry_audit(repo, countries, loc_index, all_focus=None, event_parsed=None):
    """Index local MIO/equipment/technology definitions and audit script references.

    Missing references are classified as local candidates or external dependencies;
    the base Millennium Dawn / vanilla game files are not part of this checkout.
    """
    mod = Path(repo) / "mdredux"
    country_tags = set(countries)
    mio_dir = mod / "common" / "military_industrial_organization" / "organizations"
    equipment_dir = mod / "common" / "units" / "equipment"
    technology_dir = mod / "common" / "technologies"

    mio_files = iter_files(mio_dir, ".txt")
    mio_definitions, mio_parse_errors = [], []
    local_mio_visibility_focus_candidates = []
    for path in mio_files:
        parsed = parse_hoi(read(path))
        for issue in parsed.issues:
            mio_parse_errors.append("{}:{}".format(path, issue))
        for entry in parsed.root.entries:
            if not isinstance(entry, Entry) or not isinstance(entry.value, Block):
                continue
            block = entry.value
            if not any(direct_entries(block, field) for field in
                       ("name", "allowed", "include", "initial_trait", "trait", "equipment_type")):
                continue
            match = re.match(r"^([A-Z]{3})_", entry.key.value)
            owner_tag = match.group(1) if match else None
            visible = get_block(block, "visible")
            visible_focus_refs = [
                scalar(item) for item in nested_entries(visible, "has_completed_focus")
            ] if visible else []
            visible_focus_refs = [item for item in visible_focus_refs if item]
            mio_definitions.append({
                "id": entry.key.value,
                "name": get_scalar(block, "name"),
                "include": get_scalar(block, "include"),
                "owner_tag": owner_tag,
                "path": str(path),
                "line": entry.line,
                "has_allowed": bool(direct_entries(block, "allowed")),
                "has_visible": bool(direct_entries(block, "visible")),
                "visible_focus_refs": visible_focus_refs,
                "has_initial_trait": bool(direct_entries(block, "initial_trait")),
                "trait_count": len(direct_entries(block, "trait")),
                "has_equipment_type": bool(direct_entries(block, "equipment_type")),
            })
            if visible and owner_tag in country_tags:
                for focus_entry in nested_entries(visible, "has_completed_focus"):
                    target = scalar(focus_entry)
                    if target and target not in (all_focus or set()):
                        local_mio_visibility_focus_candidates.append({
                            "mio": entry.key.value, "focus": target,
                            "path": str(path), "line": focus_entry.line,
                        })

    mio_groups = defaultdict(list)
    for item in mio_definitions:
        mio_groups[item["id"]].append(item)
    defined_mio_ids = set(mio_groups)
    duplicate_mio_ids = [
        {"id": key, "definitions": [
            {"path": item["path"], "line": item["line"]} for item in values
        ]}
        for key, values in sorted(mio_groups.items()) if len(values) > 1
    ]

    local_missing_mio_names, external_missing_mio_names = [], []
    duplicate_mio_name_keys = defaultdict(list)
    mio_name_matches_other_mio = []
    for item in mio_definitions:
        name_key = item["name"]
        if not name_key:
            continue
        duplicate_mio_name_keys[name_key].append({
            "id": item["id"], "path": item["path"], "line": item["line"],
        })
        if name_key not in loc_index:
            candidate = {
                "mio": item["id"], "name_key": name_key,
                "path": item["path"], "line": item["line"],
            }
            (local_missing_mio_names if item["owner_tag"] in country_tags
             else external_missing_mio_names).append(candidate)
        if name_key in defined_mio_ids and name_key != item["id"]:
            mio_name_matches_other_mio.append({
                "mio": item["id"], "name_key": name_key,
                "other_mio_definition": name_key,
                "path": item["path"], "line": item["line"],
            })
    duplicate_mio_name_keys = [
        {"name_key": key, "definitions": values}
        for key, values in sorted(duplicate_mio_name_keys.items()) if len(values) > 1
    ]

    equipment_files = iter_files(equipment_dir, ".txt")
    equipment_definitions, equipment_parse_errors = [], []
    for path in equipment_files:
        parsed = parse_hoi(read(path))
        for issue in parsed.issues:
            equipment_parse_errors.append("{}:{}".format(path, issue))
        for container in find_named_blocks(parsed.root, "equipments"):
            for entry in container.entries:
                if isinstance(entry, Entry) and isinstance(entry.value, Block):
                    equipment_definitions.append({
                        "id": entry.key.value, "path": str(path), "line": entry.line,
                    })
    equipment_groups = defaultdict(list)
    for item in equipment_definitions:
        equipment_groups[item["id"]].append(item)
    defined_equipment_ids = set(equipment_groups)
    duplicate_equipment_ids = [
        {"id": key, "definitions": [
            {"path": item["path"], "line": item["line"]} for item in values
        ]}
        for key, values in sorted(equipment_groups.items()) if len(values) > 1
    ]

    module_dir = equipment_dir / "modules"
    module_files = iter_files(module_dir, ".txt")
    module_ids = set()
    module_parse_errors = []
    for path in module_files:
        parsed = parse_hoi(read(path))
        for issue in parsed.issues:
            module_parse_errors.append("{}:{}".format(path, issue))
        for container in find_named_blocks(parsed.root, "equipment_modules"):
            for entry in container.entries:
                if isinstance(entry, Entry) and isinstance(entry.value, Block):
                    module_ids.add(entry.key.value)

    technology_files = iter_files(technology_dir, ".txt")
    technology_ids = set()
    technology_parse_errors = []
    for path in technology_files:
        parsed = parse_hoi(read(path))
        for issue in parsed.issues:
            technology_parse_errors.append("{}:{}".format(path, issue))
        for container in find_named_blocks(parsed.root, "technologies"):
            for entry in container.entries:
                if isinstance(entry, Entry) and isinstance(entry.value, Block):
                    technology_ids.add(entry.key.value)

    # Parse all common scripts (focuses, decisions, ideas, scripted effects, etc.) plus events.
    # Do not scan MIO/equipment definition files as usage sources.
    sources = []
    for path in iter_files(mod / "common", ".txt"):
        if mio_dir in path.parents or equipment_dir in path.parents:
            continue
        sources.append((path, parse_hoi(read(path))))
    for path, parsed in (event_parsed or {}).items():
        sources.append((Path(path), parsed))

    # Missing local technology IDs may be supplied by vanilla, base MD or DLC.
    # Keep them as explicit review candidates; never promote them to ERROR.
    unknown_technology_references = []
    seen_technology_refs = set()
    for path, parsed in sources:
        for entry in walk_entries(parsed.root):
            if entry.key.value != "has_tech":
                continue
            technology = scalar(entry)
            if technology is None and isinstance(entry.value, Block):
                technology = (
                    get_scalar(entry.value, "technology")
                    or get_scalar(entry.value, "tech")
                    or get_scalar(entry.value, "id")
                )
                if technology is None:
                    tokens = [item.value for item in entry.value.items if isinstance(item, Token)]
                    technology = tokens[0] if tokens else None
            if not technology or technology in technology_ids:
                continue
            marker = (technology, str(path), entry.line)
            if marker in seen_technology_refs:
                continue
            seen_technology_refs.add(marker)
            unknown_technology_references.append({
                "technology": technology, "command": "has_tech",
                "path": str(path), "line": entry.line,
                "classification": "not_defined_in_local_technology_slice",
            })

    mio_references, variant_definitions, stockpile_grants = [], [], []
    unknown_equipment_type_references, unknown_module_references = [], []
    invalid_stockpile_amounts = []
    seen_mio_refs = set()

    def add_mio_reference(mio_id, path, line, usage):
        ref_key = (mio_id, str(path), line, usage)
        if ref_key not in seen_mio_refs:
            seen_mio_refs.add(ref_key)
            mio_references.append({
                "mio": mio_id, "path": str(path), "line": line, "usage": usage,
            })

    for path, parsed in sources:
        for entry in walk_entries(parsed.root):
            key = entry.key.value
            key_match = re.fullmatch(r"mio:([A-Za-z0-9_]+)", key)
            if key_match:
                add_mio_reference(key_match.group(1), path, entry.line, key)
            value = scalar(entry)
            if value:
                for match in re.finditer(r"\bmio:([A-Za-z0-9_]+)\b", value):
                    add_mio_reference(match.group(1), path, entry.line, key)

        for variant in find_named_blocks(parsed.root, "create_equipment_variant"):
            type_id = get_scalar(variant, "type")
            modules = get_block(variant, "modules")
            module_refs = []
            if modules:
                for module_entry in modules.entries:
                    if not isinstance(module_entry, Entry):
                        continue
                    module_id = scalar(module_entry)
                    if not module_id or module_id.lower() in ("empty", "none"):
                        continue
                    module_refs.append(module_id)
                    if module_id not in module_ids:
                        unknown_module_references.append({
                            "module": module_id, "variant": get_scalar(variant, "name"),
                            "path": str(path), "line": module_entry.line,
                        })
            if type_id and type_id not in defined_equipment_ids:
                unknown_equipment_type_references.append({
                    "type": type_id, "action": "create_equipment_variant",
                    "variant": get_scalar(variant, "name"), "path": str(path), "line": variant.line,
                })
            variant_definitions.append({
                "name": get_scalar(variant, "name"),
                "type": type_id,
                "design_team": get_scalar(variant, "design_team"),
                "allow_without_tech": get_scalar(variant, "allow_without_tech"),
                "module_count": len(module_refs),
                "path": str(path), "line": variant.line,
            })

        for grant in find_named_blocks(parsed.root, "add_equipment_to_stockpile"):
            type_id = get_scalar(grant, "type")
            amount = get_scalar(grant, "amount")
            if type_id and type_id not in defined_equipment_ids:
                unknown_equipment_type_references.append({
                    "type": type_id, "action": "add_equipment_to_stockpile",
                    "variant": get_scalar(grant, "variant_name"), "path": str(path), "line": grant.line,
                })
            if amount is not None:
                number = numeric_value(amount)
                if number is None or number <= 0:
                    invalid_stockpile_amounts.append({
                        "amount": amount, "type": type_id, "path": str(path), "line": grant.line,
                    })
            stockpile_grants.append({
                "type": type_id,
                "amount": amount,
                "variant_name": get_scalar(grant, "variant_name"),
                "producer": get_scalar(grant, "producer"),
                "path": str(path), "line": grant.line,
            })

    missing_local_mio_references, external_mio_references = [], []
    for item in mio_references:
        if item["mio"] in defined_mio_ids:
            continue
        match = re.match(r"^([A-Z]{3})_", item["mio"])
        candidate = dict(item)
        if match and match.group(1) in country_tags:
            missing_local_mio_references.append(candidate)
        else:
            external_mio_references.append(candidate)

    local_equipment_localisation_candidates = []
    for item in equipment_definitions:
        match = re.match(r"^([A-Z]{3})_", item["id"])
        if match and match.group(1) in country_tags and item["id"] not in loc_index:
            local_equipment_localisation_candidates.append(item)

    return {
        "counts": {
            "mio_files": len(mio_files), "mio_definitions": len(mio_definitions),
            "mio_references": len(mio_references), "equipment_files": len(equipment_files),
            "equipment_ids": len(equipment_definitions), "module_files": len(module_files),
            "module_ids": len(module_ids), "technology_files": len(technology_files),
            "technology_ids": len(technology_ids), "equipment_variants": len(variant_definitions),
            "stockpile_grants": len(stockpile_grants),
        },
        "mio_parse_errors": mio_parse_errors,
        "equipment_parse_errors": equipment_parse_errors,
        "module_parse_errors": module_parse_errors,
        "technology_parse_errors": technology_parse_errors,
        "duplicate_mio_ids": duplicate_mio_ids,
        "missing_local_mio_references": missing_local_mio_references,
        "external_mio_references": external_mio_references,
        "missing_local_mio_name_localisation": local_missing_mio_names,
        "external_mio_name_localisation_candidates": external_missing_mio_names,
        "duplicate_mio_name_keys": duplicate_mio_name_keys,
        "mio_name_matches_other_mio": mio_name_matches_other_mio,
        "local_mio_visibility_focus_candidates": local_mio_visibility_focus_candidates,
        "duplicate_equipment_ids": duplicate_equipment_ids,
        "unknown_equipment_type_references": unknown_equipment_type_references,
        "unknown_module_references": unknown_module_references,
        "unknown_technology_references": unknown_technology_references,
        "invalid_stockpile_amounts": invalid_stockpile_amounts,
        "local_equipment_localisation_candidates": local_equipment_localisation_candidates,
        "mio_definitions": mio_definitions,
        "equipment_variants": variant_definitions,
        "stockpile_grants": stockpile_grants,
    }




EXTERNAL_DEPENDENCY_STATUSES = frozenset({"confirmed", "assumption", "unknown"})
EXTERNAL_DEPENDENCY_DEFAULT_SOURCES = {
    "event": "Millennium Dawn base events, another installed mod, or unresolved namespace",
    "idea": "Millennium Dawn base ideas, HOI4, DLC, or another installed module",
    "scripted_effect": "Millennium Dawn base scripted effects or another installed module",
    "scripted_trigger": "Millennium Dawn base scripted triggers or another installed module",
    "scripted_effect_or_trigger": "Millennium Dawn base scripted effects/triggers or another installed module",
    "localisation": "Millennium Dawn shared English localisation or another installed module",
    "scripted_localisation": "Millennium Dawn scripted localisation or another installed module",
    "mio": "Millennium Dawn / HOI4 DLC MIO definitions or another installed module",
    "equipment": "Millennium Dawn / HOI4 base-game or DLC equipment definitions",
    "equipment_module": "Millennium Dawn / HOI4 base-game or DLC equipment-module definitions",
    "technology": "Millennium Dawn / HOI4 base-game or DLC technology definitions",
    "decision": "Millennium Dawn base decisions or another installed module",
    "focus": "Millennium Dawn base focus trees or another installed module",
    "other": "Unknown external module; verify against the pinned baseline and active mod stack",
}


def build_external_dependency_audit(repo, event_report, decision_report, idea_report,
                                    industry_report, state_flow_report):
    """Match unresolved references against the dated external dependency registry.

    This report is diagnostic, not an allowlist: an unregistered reference remains
    visible with status=unknown, and no registry result is promoted to ERROR.
    """
    registry_path = Path(repo) / "docs" / "research" / "external-dependencies.json"
    relative_registry_path = "docs/research/external-dependencies.json"
    if not registry_path.is_file():
        return {
            "registry_available": False, "registry_path": relative_registry_path,
            "registry_validation_issues": ["external dependency registry is missing"],
            "baseline": {}, "findings": [], "unregistered_candidates": [],
            "counts": {
                "registry_entries": 0, "findings": 0, "registered_findings": 0,
                "unregistered": 0, "by_status": {}, "by_type": {},
            },
        }

    try:
        registry = json.loads(read(registry_path))
    except (ValueError, TypeError) as exc:
        raise AuditInputError("{}: некорректный JSON реестра внешних зависимостей: {}".format(
            registry_path, exc
        )) from exc
    if not isinstance(registry, dict):
        raise AuditInputError("{}: корень реестра должен быть JSON object".format(registry_path))

    validation_issues = []
    if registry.get("schema_version") != 1:
        validation_issues.append("unsupported schema_version: {!r}".format(registry.get("schema_version")))
    entries = registry.get("dependencies")
    if not isinstance(entries, list):
        raise AuditInputError("{}: поле dependencies должно быть массивом".format(registry_path))

    registry_index = {}
    valid_entries = []
    for index, dependency in enumerate(entries):
        if not isinstance(dependency, dict):
            validation_issues.append("dependencies[{}] is not an object".format(index))
            continue
        dep_type, dep_id, status = (
            dependency.get("type"), dependency.get("id"), dependency.get("status")
        )
        if not isinstance(dep_type, str) or not dep_type.strip() or not isinstance(dep_id, str) or not dep_id.strip():
            validation_issues.append("dependencies[{}] needs non-empty type and id".format(index))
            continue
        if status not in EXTERNAL_DEPENDENCY_STATUSES:
            validation_issues.append("dependencies[{}] has unsupported status {!r}".format(index, status))
            continue
        if not isinstance(dependency.get("checked_at"), str) or not dependency.get("checked_at"):
            validation_issues.append("dependencies[{}] needs checked_at".format(index))
        if not isinstance(dependency.get("expected_source"), str) or not dependency.get("expected_source"):
            validation_issues.append("dependencies[{}] needs expected_source".format(index))
        key = (dep_type, dep_id)
        if key in registry_index:
            validation_issues.append("duplicate registry entry: {} {}".format(dep_type, dep_id))
            continue
        registry_index[key] = dependency
        valid_entries.append(dependency)

    grouped = {}

    def add_reference(dep_type, identifier, reference):
        if not isinstance(identifier, str) or not identifier.strip():
            return
        identifier = identifier.strip()
        key = (dep_type, identifier)
        dependency = registry_index.get(key)
        item = grouped.get(key)
        if item is None:
            item = {
                "type": dep_type, "id": identifier,
                "status": dependency.get("status") if dependency else "unknown",
                "registry_status": "registered" if dependency else "unregistered",
                "expected_source": (
                    dependency.get("expected_source") if dependency
                    else EXTERNAL_DEPENDENCY_DEFAULT_SOURCES.get(
                        dep_type, EXTERNAL_DEPENDENCY_DEFAULT_SOURCES["other"]
                    )
                ),
                "checked_at": dependency.get("checked_at") if dependency else None,
                "verification": dependency.get("verification", []) if dependency else [],
                "notes": dependency.get("notes") if dependency else (
                    "No exact registry record. Treat as unknown until checked against the "
                    "pinned base-MD snapshot and intended game/mod stack."
                ),
                "references": [],
            }
            grouped[key] = item
        normalized = {
            field: value for field, value in reference.items()
            if value is not None and value != ""
        }
        if normalized not in item["references"]:
            item["references"].append(normalized)

    # External event calls and their external localisation keys.
    for reference in event_report.get("external_references", []):
        add_reference("event", reference.get("target"), {
            "path": reference.get("source"), "line": reference.get("line"),
            "source_kind": reference.get("source_kind"), "caller": reference.get("caller"),
            "classification": "namespace_not_defined_in_local_checkout",
        })
    for list_key in ("external_localisation", "external_option_localisation"):
        for reference in event_report.get(list_key, []):
            add_reference("localisation", reference.get("key"), {
                "path": reference.get("path"), "line": reference.get("line"),
                "source_kind": "event_localisation", "caller": reference.get("event_id"),
                "field": reference.get("field"),
            })
    for reference in event_report.get("missing_event_idea_candidates", []):
        if reference.get("classification") == "external_or_cross_country_candidate":
            add_reference("idea", reference.get("idea"), {
                "path": reference.get("path"), "line": reference.get("line"),
                "source_kind": "event", "caller": reference.get("event_id"),
                "classification": reference.get("classification"),
            })

    # External references made by decisions.
    for reference in decision_report.get("external_tooltip_localisation", []):
        add_reference("localisation", reference.get("key"), {
            "path": reference.get("path"), "line": reference.get("line"),
            "source_kind": "decision_localisation", "caller": reference.get("decision"),
        })
    for list_key, dep_type in (
        ("external_event_references", "event"),
        ("external_focus_references", "focus"),
        ("external_decision_references", "decision"),
    ):
        for reference in decision_report.get(list_key, []):
            add_reference(dep_type, reference.get("target"), {
                "path": reference.get("path"), "line": reference.get("line"),
                "source_kind": "decision", "caller": reference.get("decision"),
                "field": reference.get("field"),
            })

    # External / shared ideas, including IDs without a three-letter country prefix.
    for reference in idea_report.get("external_idea_references", []):
        add_reference("idea", reference.get("idea"), {
            "path": reference.get("path"), "line": reference.get("line"),
            "source_kind": "idea_reference", "usage": reference.get("usage"),
        })
    for reference in idea_report.get("unresolved_unprefixed_idea_references", []):
        add_reference("idea", reference.get("idea"), {
            "path": reference.get("path"), "line": reference.get("line"),
            "source_kind": "idea_reference", "usage": reference.get("usage"),
            "classification": "unprefixed_or_shared_idea_candidate",
        })

    # MIO, equipment, equipment modules and technology references.
    for list_key in ("external_mio_references", "missing_local_mio_references"):
        for reference in industry_report.get(list_key, []):
            add_reference("mio", reference.get("mio"), {
                "path": reference.get("path"), "line": reference.get("line"),
                "source_kind": "mio_reference", "usage": reference.get("usage"),
                "classification": (
                    "external_tag_candidate" if list_key == "external_mio_references"
                    else "local_tag_missing_in_checkout_or_base_dependency"
                ),
            })
    for reference in industry_report.get("external_mio_name_localisation_candidates", []):
        add_reference("localisation", reference.get("name_key"), {
            "path": reference.get("path"), "line": reference.get("line"),
            "source_kind": "mio_name", "caller": reference.get("mio"),
        })
    for reference in industry_report.get("unknown_equipment_type_references", []):
        add_reference("equipment", reference.get("type"), {
            "path": reference.get("path"), "line": reference.get("line"),
            "source_kind": reference.get("action"), "caller": reference.get("variant"),
            "classification": "not_defined_in_local_equipment_slice",
        })
    for reference in industry_report.get("unknown_module_references", []):
        add_reference("equipment_module", reference.get("module"), {
            "path": reference.get("path"), "line": reference.get("line"),
            "source_kind": "create_equipment_variant", "caller": reference.get("variant"),
            "classification": "not_defined_in_local_module_slice",
        })
    for reference in industry_report.get("unknown_technology_references", []):
        add_reference("technology", reference.get("technology"), {
            "path": reference.get("path"), "line": reference.get("line"),
            "source_kind": reference.get("command"),
            "classification": reference.get("classification"),
        })

    # Unresolved scripted calls remain candidates; the missing definition may be in base MD.
    for reference in state_flow_report.get("unresolved_scripted_call_candidates", []):
        add_reference("scripted_effect_or_trigger", reference.get("candidate"), {
            "path": reference.get("path"), "line": reference.get("line"),
            "source_kind": "scripted_call", "owner_tag": reference.get("owner_tag"),
            "classification": reference.get("classification"),
        })

    # Include explicit TDF usage entries even when the shared definition resolves locally.
    for dependency in valid_entries:
        for reference in dependency.get("where_used", []):
            if reference.get("repository") == "TDF":
                add_reference(dependency["type"], dependency["id"], {
                    **reference, "source_kind": "registry_usage",
                })

    # Expand only declared transitive dependencies (e.g. a scripted effect invoked by a
    # base event), and only if the parent is referenced by this checkout.
    used_keys = set(grouped)
    for dependency in valid_entries:
        for parent in dependency.get("related_to", []):
            if (parent.get("type"), parent.get("id")) in used_keys:
                add_reference(dependency["type"], dependency["id"], {
                    "source_kind": "transitive_dependency", "related_to": parent,
                })

    findings = sorted(grouped.values(), key=lambda item: (item["type"], item["id"].casefold()))
    for item in findings:
        item["references"].sort(key=lambda reference: (
            reference.get("path", ""), reference.get("line", 0),
            reference.get("source_kind", ""), reference.get("caller", "")
        ))
    unregistered = [item for item in findings if item["registry_status"] == "unregistered"]
    status_counts = Counter(item["status"] for item in findings)
    type_counts = Counter(item["type"] for item in findings)
    return {
        "registry_available": True, "registry_path": relative_registry_path,
        "schema_version": registry.get("schema_version"),
        "last_reviewed": registry.get("last_reviewed"),
        "baseline": registry.get("baseline", {}),
        "registry_validation_issues": validation_issues,
        "registry_entries": valid_entries, "findings": findings,
        "unregistered_candidates": unregistered,
        "counts": {
            "registry_entries": len(valid_entries), "findings": len(findings),
            "registered_findings": len(findings) - len(unregistered),
            "unregistered": len(unregistered),
            "by_status": dict(sorted(status_counts.items())),
            "by_type": dict(sorted(type_counts.items())),
        },
    }


def _state_flow_source_kind(path: Path, mod: Path) -> str:
    try:
        parts = path.relative_to(mod).parts
    except ValueError:
        parts = path.parts
    if "national_focus" in parts:
        return "focus"
    if "decisions" in parts:
        return "decision"
    if "events" in parts:
        return "event"
    if "ideas" in parts:
        return "idea"
    if "scripted_effects" in parts:
        return "scripted_effect"
    if "scripted_triggers" in parts:
        return "scripted_trigger"
    if "on_actions" in parts:
        return "on_action"
    if "history" in parts and "countries" in parts:
        return "history"
    return "common"


def _state_flow_owner_tag(path: Path, countries) -> Optional[str]:
    stem = path.stem.lower()
    for tag, country in countries.items():
        tree_name = country["tree"].name
        suffix = "_Focus_Tree.txt"
        tree_stem = tree_name[:-len(suffix)] if tree_name.endswith(suffix) else Path(tree_name).stem
        if stem == tree_stem.lower() or stem.startswith(tag.lower() + "_"):
            return tag
        if stem.startswith(tag.lower() + " ") or stem.startswith(tag.lower() + " -"):
            return tag
    match = re.match(r"^([A-Z]{3})(?:\s*[-_ ]|$)", path.name)
    if match and match.group(1) in countries:
        return match.group(1)
    return None


def _state_flow_script_files(directory: Path) -> List[Path]:
    if not directory.is_dir():
        return []
    return sorted(
        path for path in directory.rglob("*")
        if path.is_file() and (path.suffix.lower() == ".txt" or not path.suffix)
    )


def _state_flow_named_value(entry: Entry, aliases: Sequence[str]) -> Optional[str]:
    if isinstance(entry.value, Token):
        return entry.value.value
    if not isinstance(entry.value, Block):
        return None
    for alias in aliases:
        value = get_scalar(entry.value, alias)
        if value:
            return value
    return None


def _state_flow_variable_names(entry: Entry) -> List[str]:
    if isinstance(entry.value, Token):
        return [entry.value.value]
    if not isinstance(entry.value, Block):
        return []
    if entry.key.value == "compare_variables":
        values = [get_scalar(entry.value, key) for key in ("var1", "var2", "variable1", "variable2")]
        return [value for value in values if value]
    for alias in ("var", "variable"):
        value = get_scalar(entry.value, alias)
        if value:
            return [value]
    for child in entry.value.entries:
        if child.key.value not in STATE_FLOW_VARIABLE_META_KEYS and isinstance(child.value, Token):
            return [child.key.value]
    # Also accept bare comparison syntax: check_variable = { treasury > 5 }.
    for item in entry.value.items:
        if isinstance(item, Token):
            value = item.value
            if value not in (">", "<", ">=", "<=", "=", "==", "!=") and numeric_value(value) is None:
                return [value]
    return []


def _state_flow_array_name(entry: Entry) -> Optional[str]:
    if isinstance(entry.value, Token):
        return entry.value.value
    if not isinstance(entry.value, Block):
        return None
    for alias in ("array", "source_array", "target_array"):
        value = get_scalar(entry.value, alias)
        if value:
            return value
    for child in entry.value.entries:
        if child.key.value not in STATE_FLOW_ARRAY_META_KEYS and isinstance(child.value, Token):
            return child.key.value
    return None


def _state_flow_symbol_tag(symbol: str, country_tags) -> Optional[str]:
    normalized = re.sub(r"^(?:global|ROOT|FROM|PREV|THIS)\.", "", symbol)
    match = re.match(r"^([A-Z]{3})(?:_|\.|$)", normalized)
    if match and match.group(1) in country_tags:
        return match.group(1)
    return None


def _state_flow_relative(path: Path, mod: Path) -> str:
    try:
        return path.relative_to(mod).as_posix()
    except ValueError:
        return path.as_posix()


def _state_flow_entries_with_depth(block: Block, depth: int = 0):
    for item in block.items:
        if isinstance(item, Entry):
            yield item, depth
            if isinstance(item.value, Block):
                yield from _state_flow_entries_with_depth(item.value, depth + 1)


def _state_flow_effect_values(entry: Entry) -> List[str]:
    if isinstance(entry.value, Token):
        return [entry.value.value]
    if not isinstance(entry.value, Block):
        return []
    values = [item.value for item in entry.value.items if isinstance(item, Token)]
    for child in entry.value.entries:
        if child.key.value in ("idea", "add_idea") and scalar(child):
            values.append(scalar(child))
    return values


def _state_flow_entries_with_polarity(block: Block, negated: bool = False):
    """Walk entries while marking conditions nested under NOT/NOR as negative."""
    for item in block.items:
        if not isinstance(item, Entry):
            continue
        yield item, negated
        if isinstance(item.value, Block):
            child_negated = negated or item.key.value.upper() in ("NOT", "NOR")
            yield from _state_flow_entries_with_polarity(item.value, child_negated)


def _state_flow_idea_values(entry: Entry) -> List[str]:
    """Read static idea IDs from scalar, block and list-style idea commands."""
    if isinstance(entry.value, Token):
        return [entry.value.value]
    if not isinstance(entry.value, Block):
        return []
    values = [
        scalar(child) for child in entry.value.entries
        if child.key.value in ("idea", "add_idea", "has_idea") and scalar(child)
    ]
    if not values:
        values = [item.value for item in entry.value.items if isinstance(item, Token)]
    return list(dict.fromkeys(values))


def _state_flow_positive_state_reads(block: Block):
    for entry, negated in _state_flow_entries_with_polarity(block):
        if negated:
            continue
        command = entry.key.value
        if command in STATE_FLOW_FLAG_READ_KEYS:
            symbol = _state_flow_named_value(entry, ("flag", "name", "id"))
            if symbol:
                yield {
                    "family": "flag", "id": symbol, "command": command,
                    "scope": STATE_FLOW_FLAG_READ_SCOPE[command], "line": entry.line,
                }
        elif command in STATE_FLOW_IDEA_READ_KEYS:
            for symbol in _state_flow_idea_values(entry):
                yield {
                    "family": "idea", "id": symbol, "command": command,
                    "scope": None, "line": entry.line,
                }


def _state_flow_positive_state_writes(block: Block):
    for entry, _ in _state_flow_entries_with_polarity(block):
        command = entry.key.value
        if command in STATE_FLOW_FLAG_WRITE_KEYS and command.startswith("set_"):
            symbol = _state_flow_named_value(entry, ("flag", "name", "id"))
            if symbol:
                yield {
                    "family": "flag", "id": symbol, "command": command,
                    "scope": STATE_FLOW_FLAG_SCOPE.get(command), "line": entry.line,
                }
        elif command in STATE_FLOW_IDEA_WRITE_KEYS:
            for symbol in _state_flow_idea_values(entry):
                yield {
                    "family": "idea", "id": symbol, "command": command,
                    "scope": None, "line": entry.line,
                }


def _state_flow_flag_scope_matches(write_scope: Optional[str], read_scope: Optional[str]) -> Optional[bool]:
    if not write_scope or not read_scope:
        return None
    normalized_write = write_scope.replace("_timed", "")
    return normalized_write == read_scope


def build_state_flow_audit(repo, countries, event_parsed=None):
    """Build a conservative cross-file map of flags, variables, arrays and script hooks."""
    mod = Path(repo) / "mdredux"
    common_dir = mod / "common"
    country_tags = set(countries)

    history_dirs = (
        mod / "history" / "countries",
        common_dir / "history" / "countries",
    )
    history_files = sorted({
        path for directory in history_dirs for path in iter_files(directory, ".txt")
    })
    script_folders = ("scripted_effects", "scripted_triggers", "on_actions")
    script_files = {
        folder: _state_flow_script_files(common_dir / folder)
        for folder in script_folders
    }

    source_paths = set(iter_files(common_dir, ".txt"))
    source_paths.update(iter_files(mod / "events", ".txt"))
    source_paths.update(history_files)
    for paths in script_files.values():
        source_paths.update(paths)

    parsed_sources = {}
    for path in sorted(source_paths, key=lambda item: str(item)):
        if event_parsed and path in event_parsed:
            parsed_sources[path] = event_parsed[path]
        else:
            parsed_sources[path] = parse_hoi(read(path))

    source_meta = {}
    parse_errors = []
    for path, parsed in parsed_sources.items():
        owner_tag = _state_flow_owner_tag(path, countries)
        source_meta[path] = {
            "kind": _state_flow_source_kind(path, mod),
            "owner_tag": owner_tag,
            "display_path": _state_flow_relative(path, mod),
        }
        for issue in parsed.issues:
            parse_errors.append({
                "path": source_meta[path]["display_path"],
                "line": issue.line,
                "message": issue.message,
            })

    script_definition_indexes = {}
    script_definition_locations = set()
    script_parse_errors = []
    for folder, wrapper in (
        ("scripted_effects", "scripted_effects"),
        ("scripted_triggers", "scripted_triggers"),
    ):
        definitions = []
        for path in script_files[folder]:
            parsed = parsed_sources[path]
            containers = [
                entry.value for entry in direct_entries(parsed.root, wrapper)
                if isinstance(entry.value, Block)
            ] or [parsed.root]
            for container in containers:
                for entry in container.entries:
                    if isinstance(entry.value, Block):
                        item = {
                            "id": entry.key.value,
                            "path": _state_flow_relative(path, mod),
                            "line": entry.line,
                        }
                        definitions.append(item)
                        script_definition_locations.add((path, entry.line, entry.key.value, folder))
            for issue in parsed.issues:
                script_parse_errors.append({
                    "path": _state_flow_relative(path, mod),
                    "line": issue.line,
                    "message": issue.message,
                })
        script_definition_indexes[folder] = definitions

    effect_groups = defaultdict(list)
    trigger_groups = defaultdict(list)
    for item in script_definition_indexes["scripted_effects"]:
        effect_groups[item["id"]].append(item)
    for item in script_definition_indexes["scripted_triggers"]:
        trigger_groups[item["id"]].append(item)
    effect_ids, trigger_ids = set(effect_groups), set(trigger_groups)

    duplicate_effects = [
        {"id": key, "definitions": values}
        for key, values in sorted(effect_groups.items()) if len(values) > 1
    ]
    duplicate_triggers = [
        {"id": key, "definitions": values}
        for key, values in sorted(trigger_groups.items()) if len(values) > 1
    ]

    effect_calls, trigger_calls, unresolved_script_calls = [], [], []
    for path, parsed in parsed_sources.items():
        rel = source_meta.get(path, {}).get("display_path", _state_flow_relative(path, mod))
        for entry, depth in _state_flow_entries_with_depth(parsed.root):
            key = entry.key.value
            if key in effect_ids and (path, entry.line, key, "scripted_effects") not in script_definition_locations:
                effect_calls.append({"scripted_effect": key, "path": rel, "line": entry.line})
            if key in trigger_ids and (path, entry.line, key, "scripted_triggers") not in script_definition_locations:
                trigger_calls.append({"scripted_trigger": key, "path": rel, "line": entry.line})
            if (key not in effect_ids and key not in trigger_ids
                    and isinstance(entry.value, Token)
                    and entry.value.value.lower() in ("yes", "no")):
                match = re.match(r"^([A-Z]{3,5})_[A-Za-z0-9_]+$", key)
                if match:
                    tag = match.group(1)
                    unresolved_script_calls.append({
                        "candidate": key,
                        "classification": "local_definition_not_found_candidate" if tag in country_tags
                                          else "external_or_unknown_dependency",
                        "tag": tag,
                        "path": rel,
                        "line": entry.line,
                        "owner_tag": source_meta.get(path, {}).get("owner_tag"),
                    })

    unresolved_script_calls.sort(key=lambda item: (item["candidate"], item["path"], item["line"]))
    deduped_unresolved, seen_unresolved = [], set()
    for item in unresolved_script_calls:
        marker = (item["candidate"], item["path"], item["line"])
        if marker not in seen_unresolved:
            seen_unresolved.add(marker)
            deduped_unresolved.append(item)

    effect_call_counts = Counter(item["scripted_effect"] for item in effect_calls)
    trigger_call_counts = Counter(item["scripted_trigger"] for item in trigger_calls)
    unreferenced_effects = [
        {**item, "status": "no_local_call_found"}
        for item in script_definition_indexes["scripted_effects"]
        if not effect_call_counts[item["id"]]
    ]
    unreferenced_triggers = [
        {**item, "status": "no_local_call_found"}
        for item in script_definition_indexes["scripted_triggers"]
        if not trigger_call_counts[item["id"]]
    ]

    flag_records = defaultdict(lambda: {"reads": [], "writes": [], "scopes": set()})
    for path, parsed in parsed_sources.items():
        meta = source_meta[path]
        rel = meta["display_path"]
        for entry in walk_entries(parsed.root):
            key = entry.key.value
            if key in STATE_FLOW_FLAG_READ_KEYS:
                flag = _state_flow_named_value(entry, ("flag", "name", "id"))
                usage = "read"
            elif key in STATE_FLOW_FLAG_WRITE_KEYS:
                flag = _state_flow_named_value(entry, ("flag", "name", "id"))
                usage = "write"
            else:
                continue
            if not flag or flag.lower() in ("no", "none", "empty"):
                continue
            item = {
                "command": key, "path": rel, "line": entry.line,
                "owner_tag": meta["owner_tag"], "source_kind": meta["kind"],
            }
            flag_records[flag]["scopes"].add(STATE_FLOW_FLAG_SCOPE.get(key, key.replace("has_", "")))
            flag_records[flag]["reads" if usage == "read" else "writes"].append(item)

    flag_symbols, potentially_unread_flags, flags_read_without_local_writer = [], [], []
    for flag, record in sorted(flag_records.items()):
        local_tag = _state_flow_symbol_tag(flag, country_tags)
        if not local_tag:
            continue
        item = {
            "id": flag, "local_tag": local_tag, "scopes": sorted(record["scopes"]),
            "read_count": len(record["reads"]), "write_count": len(record["writes"]),
            "reads": record["reads"][:20], "writes": record["writes"][:20],
        }
        flag_symbols.append(item)
        if record["writes"] and not record["reads"]:
            potentially_unread_flags.append({
                "flag": flag, "tag": local_tag, "writes": record["writes"][:10],
                "status": "no_reader_in_available_checkout_external_reader_possible",
            })
        elif record["reads"] and not record["writes"]:
            flags_read_without_local_writer.append({
                "flag": flag, "tag": local_tag, "reads": record["reads"][:10],
                "status": "no_writer_in_available_checkout_external_initialisation_possible",
            })

    variable_records = defaultdict(lambda: {"reads": [], "writes": [], "operations": set()})
    for path, parsed in parsed_sources.items():
        meta = source_meta[path]
        rel = meta["display_path"]
        for entry in walk_entries(parsed.root):
            command = entry.key.value
            if command in STATE_FLOW_VARIABLE_WRITE_KEYS:
                names = _state_flow_variable_names(entry)
                for variable in names:
                    record = variable_records[variable]
                    record["writes"].append({
                        "command": command, "path": rel, "line": entry.line,
                        "owner_tag": meta["owner_tag"], "source_kind": meta["kind"],
                    })
                    record["operations"].add(command)
                    if command in ("add_to_variable", "subtract_from_variable", "multiply_variable",
                                   "divide_variable", "clamp_variable", "modulo_variable"):
                        record["reads"].append({
                            "command": command, "path": rel, "line": entry.line,
                            "owner_tag": meta["owner_tag"], "source_kind": meta["kind"],
                        })
            elif command in STATE_FLOW_VARIABLE_READ_KEYS:
                for variable in _state_flow_variable_names(entry):
                    variable_records[variable]["reads"].append({
                        "command": command, "path": rel, "line": entry.line,
                        "owner_tag": meta["owner_tag"], "source_kind": meta["kind"],
                    })
        for entry in walk_entries(parsed.root):
            value = scalar(entry)
            if not value:
                continue
            for match in re.finditer(r"\b(?:var|global_var):([A-Za-z0-9_.^]+)", value):
                variable = match.group(1)
                variable_records[variable]["reads"].append({
                    "command": "variable_expression", "path": rel, "line": entry.line,
                    "owner_tag": meta["owner_tag"], "source_kind": meta["kind"],
                })

    variable_symbols, potentially_unread_variables, variables_read_without_local_writer = [], [], []
    for variable, record in sorted(variable_records.items()):
        local_tag = _state_flow_symbol_tag(variable, country_tags)
        if not local_tag:
            continue
        variable_symbols.append({
            "id": variable, "local_tag": local_tag,
            "read_count": len(record["reads"]), "write_count": len(record["writes"]),
            "operations": sorted(record["operations"]),
            "reads": record["reads"][:20], "writes": record["writes"][:20],
        })
        if record["writes"] and not record["reads"]:
            potentially_unread_variables.append({
                "variable": variable, "tag": local_tag, "writes": record["writes"][:10],
                "status": "no_reader_in_available_checkout_external_reader_possible",
            })
        elif record["reads"] and not record["writes"]:
            variables_read_without_local_writer.append({
                "variable": variable, "tag": local_tag, "reads": record["reads"][:10],
                "status": "no_writer_in_available_checkout_external_initialisation_possible",
            })

    array_records = defaultdict(lambda: {"reads": [], "writes": [], "operations": set()})
    for path, parsed in parsed_sources.items():
        meta = source_meta[path]
        rel = meta["display_path"]
        for entry in walk_entries(parsed.root):
            command = entry.key.value
            if command in STATE_FLOW_ARRAY_WRITE_KEYS:
                array_name = _state_flow_array_name(entry)
                if array_name:
                    record = array_records[array_name]
                    record["writes"].append({
                        "command": command, "path": rel, "line": entry.line,
                        "owner_tag": meta["owner_tag"], "source_kind": meta["kind"],
                    })
                    record["operations"].add(command)
                    if command == "remove_from_array":
                        record["reads"].append({
                            "command": command, "path": rel, "line": entry.line,
                            "owner_tag": meta["owner_tag"], "source_kind": meta["kind"],
                        })
            elif command in STATE_FLOW_ARRAY_READ_KEYS and isinstance(entry.value, Block):
                array_name = _state_flow_array_name(entry)
                if array_name:
                    array_records[array_name]["reads"].append({
                        "command": command, "path": rel, "line": entry.line,
                        "owner_tag": meta["owner_tag"], "source_kind": meta["kind"],
                    })

    array_symbols, potentially_unread_arrays, arrays_read_without_local_writer = [], [], []
    for array_name, record in sorted(array_records.items()):
        local_tag = _state_flow_symbol_tag(array_name, country_tags)
        if not local_tag:
            continue
        array_symbols.append({
            "id": array_name, "local_tag": local_tag,
            "read_count": len(record["reads"]), "write_count": len(record["writes"]),
            "operations": sorted(record["operations"]),
            "reads": record["reads"][:20], "writes": record["writes"][:20],
        })
        if record["writes"] and not record["reads"]:
            potentially_unread_arrays.append({
                "array": array_name, "tag": local_tag, "writes": record["writes"][:10],
                "status": "no_reader_in_available_checkout_external_reader_possible",
            })
        elif record["reads"] and not record["writes"]:
            arrays_read_without_local_writer.append({
                "array": array_name, "tag": local_tag, "reads": record["reads"][:10],
                "status": "no_writer_in_available_checkout_external_initialisation_possible",
            })

    idea_on_add_without_matching_on_remove = []
    idea_files = _state_flow_script_files(common_dir / "ideas")
    for path in idea_files:
        if path.suffix.lower() != ".txt":
            continue
        parsed = parsed_sources.get(path)
        if parsed is None:
            parsed = parse_hoi(read(path))
        for ideas_block in find_named_blocks(parsed.root, "ideas"):
            for group_name in ("country", "hidden_ideas"):
                for group_entry in direct_entries(ideas_block, group_name):
                    if not isinstance(group_entry.value, Block):
                        continue
                    for idea_entry in group_entry.value.entries:
                        if not isinstance(idea_entry.value, Block):
                            continue
                        idea_block = idea_entry.value
                        on_add = get_block(idea_block, "on_add")
                        on_remove = get_block(idea_block, "on_remove")
                        if on_add is None:
                            continue

                        def collect_mutations(effect_block):
                            found = []
                            if effect_block is None:
                                return found
                            for op_entry in walk_entries(effect_block):
                                command = op_entry.key.value
                                if command in STATE_FLOW_FLAG_WRITE_KEYS and not command.startswith("set_timed_"):
                                    symbol = _state_flow_named_value(op_entry, ("flag", "name", "id"))
                                    family = "flag"
                                elif command in STATE_FLOW_VARIABLE_WRITE_KEYS:
                                    names = _state_flow_variable_names(op_entry)
                                    symbol = names[0] if names else None
                                    family = "variable"
                                elif command in STATE_FLOW_ARRAY_WRITE_KEYS:
                                    symbol = _state_flow_array_name(op_entry)
                                    family = "array"
                                else:
                                    continue
                                if symbol:
                                    found.append({"family": family, "id": symbol, "command": command,
                                                  "line": op_entry.line})
                            return found

                        adds = collect_mutations(on_add)
                        removes = collect_mutations(on_remove)
                        inverse = {
                            "set_country_flag": "clr_country_flag", "set_global_flag": "clr_global_flag",
                            "set_state_flag": "clr_state_flag", "set_province_flag": "clr_province_flag",
                            "add_to_array": "remove_from_array", "remove_from_array": "add_to_array",
                            "add_to_variable": "subtract_from_variable", "subtract_from_variable": "add_to_variable",
                        }
                        for mutation in adds:
                            command = mutation["command"]
                            if command in inverse:
                                matched = any(
                                    item["family"] == mutation["family"] and item["id"] == mutation["id"]
                                    and item["command"] == inverse[command] for item in removes
                                )
                            elif command in ("set_variable", "set_temp_variable"):
                                matched = any(
                                    item["family"] == "variable" and item["id"] == mutation["id"]
                                    and item["command"] in ("set_variable", "set_temp_variable")
                                    for item in removes
                                )
                            else:
                                matched = True
                            if not matched:
                                idea_on_add_without_matching_on_remove.append({
                                    "idea": idea_entry.key.value, "family": mutation["family"],
                                    "id": mutation["id"], "on_add_command": command,
                                    "path": _state_flow_relative(path, mod),
                                    "line": mutation["line"],
                                    "status": "manual_review_one_sided_state_change",
                                })

    # Link direct flag/idea writes in decision and event effects to positive gates
    # in other objects. This graph is diagnostic evidence, not runtime proof.
    state_writers = defaultdict(list)
    state_readers = defaultdict(list)

    def register_state_refs(bucket, extractor, block, metadata, object_key):
        for item in extractor(block):
            local_tag = _state_flow_symbol_tag(item["id"], country_tags)
            if not local_tag:
                continue
            bucket[(item["family"], item["id"])].append({
                **item, **metadata, "object_key": object_key, "local_tag": local_tag,
            })

    for path, parsed in parsed_sources.items():
        meta = source_meta[path]
        rel = meta["display_path"]
        if meta["kind"] == "decision":
            for category_entry in parsed.root.entries:
                if not isinstance(category_entry, Entry) or not isinstance(category_entry.value, Block):
                    continue
                category_id = category_entry.key.value
                category_block = category_entry.value
                for gate in ("potential", "allowed", "visible"):
                    for gate_entry in direct_entries(category_block, gate):
                        if isinstance(gate_entry.value, Block):
                            key = "decision_category|{}|{}|{}".format(rel, category_id, gate)
                            register_state_refs(
                                state_readers, _state_flow_positive_state_reads, gate_entry.value,
                                {"object_kind": "decision_category", "object_id": category_id,
                                 "category": category_id, "gate": gate, "path": rel,
                                 "owner_tag": meta["owner_tag"]},
                                key,
                            )
                for decision_entry in category_block.entries:
                    if (not isinstance(decision_entry, Entry)
                            or not isinstance(decision_entry.value, Block)
                            or decision_entry.key.value in DECISION_CATEGORY_FIELDS):
                        continue
                    decision_id = decision_entry.key.value
                    decision_block = decision_entry.value
                    for gate in ("visible", "available", "allowed", "activation"):
                        for gate_entry in direct_entries(decision_block, gate):
                            if isinstance(gate_entry.value, Block):
                                key = "decision|{}|{}|{}|{}".format(rel, category_id, decision_id, gate)
                                register_state_refs(
                                    state_readers, _state_flow_positive_state_reads, gate_entry.value,
                                    {"object_kind": "decision", "object_id": decision_id,
                                     "category": category_id, "gate": gate, "path": rel,
                                     "owner_tag": meta["owner_tag"]},
                                    key,
                                )
                    for effect in ("complete_effect", "remove_effect", "timeout_effect", "cancel_effect"):
                        for effect_entry in direct_entries(decision_block, effect):
                            if isinstance(effect_entry.value, Block):
                                key = "decision|{}|{}|{}|{}".format(rel, category_id, decision_id, effect)
                                register_state_refs(
                                    state_writers, _state_flow_positive_state_writes, effect_entry.value,
                                    {"object_kind": "decision", "object_id": decision_id,
                                     "category": category_id, "effect": effect, "path": rel,
                                     "owner_tag": meta["owner_tag"]},
                                    key,
                                )
        elif meta["kind"] == "event":
            for event_kind in ("country_event", "news_event"):
                for event_entry in direct_entries(parsed.root, event_kind):
                    if not isinstance(event_entry.value, Block):
                        continue
                    event_block = event_entry.value
                    event_id = get_scalar(event_block, "id")
                    if not event_id:
                        continue
                    for gate_entry in direct_entries(event_block, "trigger"):
                        if isinstance(gate_entry.value, Block):
                            key = "event|{}|{}|trigger".format(rel, event_id)
                            register_state_refs(
                                state_readers, _state_flow_positive_state_reads, gate_entry.value,
                                {"object_kind": "event", "object_id": event_id,
                                 "gate": "trigger", "path": rel,
                                 "owner_tag": meta["owner_tag"], "event_kind": event_kind},
                                key,
                            )
                    for immediate_entry in direct_entries(event_block, "immediate"):
                        if isinstance(immediate_entry.value, Block):
                            key = "event|{}|{}|immediate".format(rel, event_id)
                            register_state_refs(
                                state_writers, _state_flow_positive_state_writes, immediate_entry.value,
                                {"object_kind": "event", "object_id": event_id,
                                 "effect": "immediate", "path": rel,
                                 "owner_tag": meta["owner_tag"], "event_kind": event_kind},
                                key,
                            )
                    for option_entry in direct_entries(event_block, "option"):
                        if not isinstance(option_entry.value, Block):
                            continue
                        option_name = get_scalar(option_entry.value, "name") or "(unnamed option)"
                        for gate_entry in direct_entries(option_entry.value, "trigger"):
                            if isinstance(gate_entry.value, Block):
                                key = "event_option|{}|{}|{}|trigger".format(rel, event_id, option_name)
                                register_state_refs(
                                    state_readers, _state_flow_positive_state_reads, gate_entry.value,
                                    {"object_kind": "event_option", "object_id": event_id,
                                     "option": option_name, "gate": "trigger", "path": rel,
                                     "owner_tag": meta["owner_tag"], "event_kind": event_kind},
                                    key,
                                )
                        key = "event_option|{}|{}|{}|effect".format(rel, event_id, option_name)
                        register_state_refs(
                            state_writers, _state_flow_positive_state_writes, option_entry.value,
                            {"object_kind": "event_option", "object_id": event_id,
                             "option": option_name, "effect": "option", "path": rel,
                             "owner_tag": meta["owner_tag"], "event_kind": event_kind},
                            key,
                        )

    decision_event_state_links = []
    for (family, symbol), writers in sorted(state_writers.items()):
        readers = state_readers.get((family, symbol), [])
        if not readers:
            continue
        for writer in writers:
            for reader in readers:
                same_event = (
                    writer["object_kind"] in ("event", "event_option")
                    and reader["object_kind"] in ("event", "event_option")
                    and writer["object_id"] == reader["object_id"]
                )
                if writer["object_key"] == reader["object_key"] or same_event:
                    continue
                scope_match = (
                    _state_flow_flag_scope_matches(writer.get("scope"), reader.get("scope"))
                    if family == "flag" else None
                )
                decision_event_state_links.append({
                    "family": family, "id": symbol, "local_tag": writer["local_tag"],
                    "relationship": "{}_to_{}".format(
                        writer["object_kind"].replace("_option", ""),
                        reader["object_kind"].replace("_option", ""),
                    ),
                    "status": (
                        "same_id_scope_mismatch_candidate"
                        if scope_match is False else "same_id_cross_object_candidate"
                    ),
                    "scope_match": scope_match,
                    "writer": {key: value for key, value in writer.items()
                               if key not in ("object_key", "family", "id", "scope", "local_tag")},
                    "reader": {key: value for key, value in reader.items()
                               if key not in ("object_key", "family", "id", "scope", "local_tag")},
                })
    decision_event_state_links.sort(
        key=lambda item: (item["local_tag"], item["family"], item["id"],
                          item["writer"]["path"], item["writer"]["line"],
                          item["reader"]["path"], item["reader"]["line"])
    )

    on_action_hooks = []
    for path in script_files["on_actions"]:
        parsed = parsed_sources[path]
        containers = [
            entry.value for entry in direct_entries(parsed.root, "on_actions")
            if isinstance(entry.value, Block)
        ] or [parsed.root]
        for container in containers:
            for entry in container.entries:
                if isinstance(entry.value, Block):
                    on_action_hooks.append({
                        "id": entry.key.value, "path": _state_flow_relative(path, mod), "line": entry.line,
                    })

    history_summaries, history_tags = [], set()
    for path in history_files:
        parsed = parsed_sources[path]
        tag = _state_flow_owner_tag(path, countries)
        if tag:
            history_tags.add(tag)
        date_blocks = [
            entry for entry in parsed.root.entries
            if isinstance(entry, Entry) and isinstance(entry.value, Block)
            and re.fullmatch(r"\d{4}\.\d{1,2}\.\d{1,2}", entry.key.value)
        ]
        idea_grants, variable_initialisations = [], []
        for date_entry in date_blocks:
            for item in walk_entries(date_entry.value):
                if item.key.value in ("add_ideas", "add_idea"):
                    for idea_id in _state_flow_effect_values(item):
                        idea_grants.append({
                            "idea": idea_id, "date": date_entry.key.value,
                            "path": _state_flow_relative(path, mod), "line": item.line,
                        })
                elif item.key.value in ("add_timed_idea",) and isinstance(item.value, Block):
                    idea_id = get_scalar(item.value, "idea")
                    if idea_id:
                        idea_grants.append({
                            "idea": idea_id, "date": date_entry.key.value,
                            "path": _state_flow_relative(path, mod), "line": item.line,
                            "timed": True,
                        })
                elif item.key.value in ("set_variable", "set_temp_variable"):
                    for variable in _state_flow_variable_names(item):
                        variable_initialisations.append({
                            "variable": variable, "command": item.key.value, "date": date_entry.key.value,
                            "path": _state_flow_relative(path, mod), "line": item.line,
                        })
        history_summaries.append({
            "tag": tag, "path": _state_flow_relative(path, mod),
            "date_blocks": len(date_blocks),
            "first_date": date_blocks[0].key.value if date_blocks else None,
            "startup_idea_grants": idea_grants,
            "startup_variable_initialisations": variable_initialisations,
            "startup_event_calls": [
                {"kind": kind, "id": event_id, "line": line}
                for kind, event_id, line in iter_event_calls(parsed.root)
            ],
        })

    missing_history_tags = sorted(country_tags - history_tags) if history_files else sorted(country_tags)
    scope_usage_counts = Counter()
    for parsed in parsed_sources.values():
        for entry in walk_entries(parsed.root):
            value = scalar(entry) or ""
            for scope in re.findall(r"\b(ROOT|FROM|PREV|THIS)\.", value):
                scope_usage_counts[scope] += 1

    return {
        "counts": {
            "source_files": len(parsed_sources), "history_files": len(history_files),
            "history_tags": len(history_tags),
            "scripted_effect_files": len(script_files["scripted_effects"]),
            "scripted_effect_definitions": len(script_definition_indexes["scripted_effects"]),
            "scripted_effect_calls": len(effect_calls),
            "scripted_trigger_files": len(script_files["scripted_triggers"]),
            "scripted_trigger_definitions": len(script_definition_indexes["scripted_triggers"]),
            "scripted_trigger_calls": len(trigger_calls),
            "on_action_files": len(script_files["on_actions"]), "on_action_hooks": len(on_action_hooks),
            "flag_symbols": len(flag_symbols), "variable_symbols": len(variable_symbols),
            "array_symbols": len(array_symbols),
            "decision_event_state_links": len(decision_event_state_links),
        },
        "parse_errors": parse_errors, "script_parse_errors": script_parse_errors,
        "duplicate_scripted_effect_definitions": duplicate_effects,
        "duplicate_scripted_trigger_definitions": duplicate_triggers,
        "scripted_effect_calls": effect_calls, "scripted_trigger_calls": trigger_calls,
        "scripted_effects_without_local_call": unreferenced_effects,
        "scripted_triggers_without_local_call": unreferenced_triggers,
        "unresolved_scripted_call_candidates": deduped_unresolved,
        "flag_symbols": flag_symbols,
        "potentially_unread_local_flags": potentially_unread_flags,
        "local_flags_read_without_writer": flags_read_without_local_writer,
        "variable_symbols": variable_symbols,
        "potentially_unread_local_variables": potentially_unread_variables,
        "local_variables_read_without_writer": variables_read_without_local_writer,
        "array_symbols": array_symbols,
        "decision_event_state_links": decision_event_state_links,
        "potentially_unread_local_arrays": potentially_unread_arrays,
        "local_arrays_read_without_writer": arrays_read_without_local_writer,
        "idea_on_add_without_matching_on_remove": idea_on_add_without_matching_on_remove,
        "on_action_hooks": on_action_hooks,
        "on_action_inventory_available": bool(script_files["on_actions"]),
        "scripted_trigger_inventory_available": bool(script_files["scripted_triggers"]),
        "history_inventory_available": bool(history_files),
        "history_tags": sorted(history_tags), "history_summaries": history_summaries,
        "countries_without_local_history": [
            {"tag": tag, "status": "unknown_or_external_history_not_in_checkout"}
            for tag in missing_history_tags
        ],
        "scope_usage_counts": dict(sorted(scope_usage_counts.items())),
        "scope_analysis_limit": (
            "Static indexing does not resolve ROOT/FROM/PREV/THIS or prove that a scripted effect "
            "is called by the base mod. Treat unreferenced definitions and unmatched lifecycle "
            "mutations as review candidates, not automatic errors."
        ),
    }


def audit_country(tag, country, loc_index, all_focus, known_tags, defined_events, defined_namespaces, event_parsed, content_indexes):
    source = country["tree_source"]
    parsed = country["tree_parsed"]
    R = defaultdict(list)
    R["space_indent_lines"] = sum(1 for line in source.splitlines() if re.match(r"^ +\S", line))
    R["brace_balance"] = parsed.brace_balance
    for issue in parsed.issues:
        R["parse_errors"].append("{}:{}".format(country["tree"].name, issue))

    duplicate_keys = [key for key, occurrences in loc_index.items() if len(occurrences) > 1 and key.startswith(tag + "_")]
    R["dup_loc_keys"] = sorted(duplicate_keys)
    for issue in content_indexes["script_parse_errors"].get(tag, []):
        R["parse_errors"].append(issue)

    defined_ideas = content_indexes["idea_ids"].get(tag, set())

    definitions = content_indexes["scripted_defs"].get(tag, [])
    definition_counts = Counter(definition["name"] for definition in definitions)
    R["scripted_loc_duplicate"] = sorted(name for name, count in definition_counts.items() if count > 1)
    defined_scripted_names = set(definition_counts)
    referenced_scripted_names = content_indexes["scripted_refs"].get(tag, set())
    for name in sorted(referenced_scripted_names - defined_scripted_names):
        R["scripted_loc_missing"].append(name)
    for name in sorted(defined_scripted_names - referenced_scripted_names):
        R["scripted_loc_unused"].append(name)
    for definition in definitions:
        for loc_key in definition["localization_keys"]:
            if loc_key.startswith(tag + "_") and loc_key not in loc_index:
                R["scripted_loc_loc_missing"].append((definition["name"], loc_key))
        for idea_ref in definition["idea_refs"]:
            if idea_ref.startswith(tag + "_") and idea_ref not in defined_ideas:
                R["scripted_loc_idea_missing"].append((definition["name"], idea_ref))

    focuses = []
    for body in find_named_blocks(parsed.root, "focus"):
        fid = get_scalar(body, "id")
        if fid:
            focuses.append((fid, body))
    hidden = {fid for fid, body in focuses if has_disabled_allow_branch(body)}
    changed = True
    while changed:
        changed = False
        for fid, body in focuses:
            prereqs = focus_prerequisite_ids(body)
            # Conservative: mark hidden only when every referenced prerequisite is hidden.
            # This avoids treating an OR path with a visible alternative as inaccessible.
            if fid not in hidden and prereqs and all(prereq in hidden for prereq in prereqs):
                hidden.add(fid)
                changed = True
    R["hidden_branch_focus"] = sorted(hidden)

    focus_counts = Counter(fid for fid, _ in focuses)
    R["dup_focus_ids"] = sorted(fid for fid, count in focus_counts.items() if count > 1)
    lengths = []
    for fid, body in focuses:
        for candidate in idea_candidates(body):
            if candidate.startswith(tag + "_") and candidate not in defined_ideas:
                R["idea_not_found"].append((fid, candidate))
        reward = get_block(body, "completion_reward")
        log_value = get_scalar(reward, "log") if reward else None
        log_match = re.search(r"[Ff]ocus\s+([A-Za-z0-9_.-]+)", log_value or "")
        if reward and not log_match:
            R["no_log"].append(fid)
        elif log_match and log_match.group(1) not in (fid, "executed"):
            R["log_mismatch"].append((fid, log_match.group(1)))

        for prerequisite in focus_prerequisite_ids(body):
            if prerequisite not in all_focus:
                R["prereq_missing"].append((fid, prerequisite))
        for mutex in direct_entries(body, "mutually_exclusive"):
            if isinstance(mutex.value, Block):
                for entry in nested_entries(mutex.value, "focus"):
                    ref = scalar(entry)
                    if ref and ref not in all_focus:
                        R["mutex_missing"].append((fid, ref))
        relpos = get_scalar(body, "relative_position_id")
        if relpos and relpos not in all_focus:
            R["relpos_missing"].append((fid, relpos))

        title = get_loc_value(loc_index, fid)
        desc = get_loc_value(loc_index, fid + "_desc")
        if fid not in hidden:
            if title is None:
                R["title_missing"].append(fid)
            if desc is None:
                R["desc_missing"].append(fid)
        if title and len(title) > 30:
            R["title_gt30"].append((fid, len(title)))
        if desc:
            lengths.append(len(desc))
            if len(desc) < 150:
                R["desc_lt150"].append((fid, len(desc)))
            if len(desc) > 340:
                R["desc_gt340"].append((fid, len(desc)))
            low = desc.lower()
            hits = [phrase for phrase in BANNED if phrase in low]
            if BANNED_WORD.search(desc):
                hits.append("key")
            if hits:
                R["banned_phrase"].append((fid, ", ".join(hits)))

        if reward:
            non_log_entries = [entry for entry in reward.entries if entry.key.value != "log"]
            if not non_log_entries:
                R["empty_reward"].append(fid)
            for sf in direct_entries(body, "search_filters"):
                if isinstance(sf.value, Block):
                    for item in sf.value.items:
                        if isinstance(item, Token) and not item.value.startswith("FOCUS_FILTER_"):
                            R["nonstandard_filter"].append((fid, item.value))
            # Pair remove/add only inside the same swap_ideas block. Pairing all
            # nested commands globally can create false matches across separate swaps.
            for swap in find_named_blocks(reward, "swap_ideas"):
                old = get_scalar(swap, "remove_idea")
                new = get_scalar(swap, "add_idea")
                if old and old == new:
                    R["swap_same_idea"].append((fid, old))
            for tech_bonus in find_named_blocks(reward, "add_tech_bonus"):
                if not any(entry.key.value == "uses" for entry in tech_bonus.entries):
                    R["tech_bonus_no_uses"].append(fid)
            for _, event_id, _line in iter_event_calls(reward):
                if event_id in defined_events:
                    continue
                namespace = event_id.split(".", 1)[0] if "." in event_id else ""
                if namespace and namespace in defined_namespaces:
                    R["event_not_found"].append((fid, event_id))
                else:
                    R["event_external"].append((fid, event_id))

            for candidate in idea_candidates(reward):
                match = re.match(r"^([A-Z]{3})_[A-Za-z0-9_]+$", candidate)
                if match and match.group(1) in known_tags and match.group(1) != tag:
                    R["foreign_tag_ref"].append((fid, candidate))

            if "effect_tooltip" in {entry.key.value for entry in walk_entries(reward)}:
                action_keys = {entry.key.value for entry in walk_entries(reward)}
                real_effects = {"add_", "set_", "modify_", "change_"}
                has_effect = any(key.startswith(tuple(real_effects)) for key in action_keys)
                if not has_effect and len(repr(reward.items)) < 600:
                    R["tooltip_only_reward"].append(fid)

    R["n_focus"] = len(focuses)
    R["desc_median"] = st.median(lengths) if lengths else 0

    # Audit event options from this country's associated event file, if present.
    event_path = country["events"]
    ep = event_parsed.get(event_path) if event_path else None
    if ep:
        for issue in ep.issues:
            R["parse_errors"].append("{}:{}".format(event_path.name, issue))
        for kind in ("country_event", "news_event"):
            for event_entry in direct_entries(ep.root, kind):
                if not isinstance(event_entry.value, Block):
                    continue
                event_block = event_entry.value
                event_id = get_scalar(event_block, "id") or "?"
                for candidate in idea_candidates(event_block):
                    if candidate.startswith(tag + "_") and candidate not in defined_ideas:
                        R["idea_not_found"].append((event_id, candidate))
                for field in ("title", "desc"):
                    loc_key = get_scalar(event_block, field)
                    if loc_key and loc_key not in loc_index:
                        if is_local_event_key(loc_key, event_id, tag):
                            R["event_{}_key_missing".format(field)].append((event_id, loc_key))
                        else:
                            R["event_{}_key_external".format(field)].append((event_id, loc_key))
                if get_scalar(event_block, "picture") is None:
                    R["event_without_picture"].append(event_id)
                for option_entry in direct_entries(event_block, "option"):
                    if not isinstance(option_entry.value, Block):
                        continue
                    option = option_entry.value
                    label_key = get_scalar(option, "name")
                    label = get_loc_value(loc_index, label_key) if label_key else None
                    if label is None and label_key:
                        if is_local_event_key(label_key, event_id, tag):
                            R["event_option_label_missing"].append(label_key)
                        else:
                            # Generic/base-mod labels may live outside this repository slice.
                            R["event_option_label_external"].append(label_key)
                    if label:
                        if label.strip().rstrip(".!?").lower() in GENERIC_LABELS:
                            R["event_generic_label"].append(label)
                        elif len(label) > 35:
                            R["event_label_gt35"].append(label[:40])
                    if get_scalar(option, "log") is None:
                        R["event_option_no_log"].append(label_key or "?")
    return R


def _branch_values(entry: Entry) -> List[str]:
    """Read scalar or bare-list values from an idea effect/condition entry."""
    if isinstance(entry.value, Token):
        return [entry.value.value]
    if not isinstance(entry.value, Block):
        return []
    values = []
    for item in entry.value.items:
        if isinstance(item, Token):
            if item.value.lower() not in ("yes", "no", "none", "empty"):
                values.append(item.value)
        elif isinstance(item, Entry) and item.key.value in ("idea", "add_idea", "remove_idea"):
            value = scalar(item)
            if value:
                values.append(value)
    return values


def _branch_idea_effects(block: Optional[Block]) -> List[Dict[str, str]]:
    """Collect explicit idea grants/removals, excluding has_idea conditions."""
    if block is None:
        return []
    result = []
    for entry in walk_entries(block):
        command = entry.key.value
        if command in ("add_ideas", "add_idea", "remove_ideas", "remove_idea"):
            usage = "grant" if command.startswith("add_") else "remove"
            for idea_id in _branch_values(entry):
                result.append({"idea": idea_id, "usage": usage, "command": command, "line": entry.line})
        elif command == "add_timed_idea" and isinstance(entry.value, Block):
            idea_id = get_scalar(entry.value, "idea")
            if idea_id:
                result.append({"idea": idea_id, "usage": "timed_grant",
                               "command": command, "line": entry.line})
    return result


def _branch_idea_gates(block: Optional[Block]) -> List[Dict[str, str]]:
    if block is None:
        return []
    result = []
    # Reuse the state-flow polarity walker: a has_idea inside NOT/NOR is not
    # evidence that the object requires the idea to proceed.
    for reference in _state_flow_positive_state_reads(block):
        if reference["family"] != "idea":
            continue
        result.append({
            "idea": reference["id"], "command": reference["command"], "line": reference["line"],
        })
    return result


def _branch_mio_references(block: Block) -> List[str]:
    found = set()
    for entry in walk_entries(block):
        for value in (entry.key.value, scalar(entry) or ""):
            found.update(re.findall(r"\bmio:([A-Za-z0-9_]+)\b", value))
    return sorted(found)


def _branch_equipment_outputs(block: Optional[Block]) -> List[Dict[str, str]]:
    if block is None:
        return []
    result = []
    for variant in find_named_blocks(block, "create_equipment_variant"):
        result.append({
            "kind": "variant", "name": get_scalar(variant, "name") or "",
            "equipment": get_scalar(variant, "type") or "", "line": variant.line,
        })
    for grant in find_named_blocks(block, "add_equipment_to_stockpile"):
        result.append({
            "kind": "stockpile", "name": get_scalar(grant, "variant_name") or "",
            "equipment": get_scalar(grant, "type") or "", "amount": get_scalar(grant, "amount") or "",
            "producer": get_scalar(grant, "producer") or "", "line": grant.line,
        })
    return result


def build_branch_connectivity_audit(countries, event_report, idea_report, industry_report,
                                    state_flow_report, event_parsed, content_indexes,
                                    loc_index, tags=None):
    """Assemble typed evidence edges across focus, event, idea, tooltip, MIO and state flow.

    This is a static cross-reference map. Candidate handoffs are review aids, not
    proof of runtime reachability and never affect the auditor exit code.
    """
    wanted = set(tags or countries)
    wanted &= set(countries)
    focus_by_tag = {}
    focus_lookup = {}
    focus_prerequisite_edges = []
    focus_event_edges = []
    focus_idea_grant_edges = []
    focus_idea_gate_edges = []
    focus_equipment_edges = []
    focus_mio_edges = []
    focus_nodes_by_tag = {}

    for tag in sorted(wanted):
        country = countries[tag]
        focus_nodes = []
        focus_bodies = {}
        for body in find_named_blocks(country["tree_parsed"].root, "focus"):
            focus_id = get_scalar(body, "id")
            if not focus_id:
                continue
            focus_bodies[focus_id] = body
            focus_lookup[focus_id] = (tag, body)
            focus_nodes.append({
                "id": focus_id, "path": str(country["tree"]), "line": body.line,
                "relative_position_id": get_scalar(body, "relative_position_id"),
                "prerequisites": focus_prerequisite_ids(body),
                "has_completion_reward": bool(direct_entries(body, "completion_reward")),
                "has_hidden_effect": bool(direct_entries(body, "hidden_effect")),
            })
            for prerequisite in focus_prerequisite_ids(body):
                focus_prerequisite_edges.append({
                    "tag": tag, "from": prerequisite, "to": focus_id,
                    "relation": "prerequisite", "path": str(country["tree"]), "line": body.line,
                })

            for field in ("completion_reward", "hidden_effect"):
                for effect_entry in direct_entries(body, field):
                    if not isinstance(effect_entry.value, Block):
                        continue
                    for output in _branch_idea_effects(effect_entry.value):
                        if output["usage"] in ("grant", "timed_grant"):
                            focus_idea_grant_edges.append({
                                "tag": tag, "from": focus_id, "to": output["idea"],
                                "relation": output["usage"], "command": output["command"],
                                "path": str(country["tree"]), "line": output["line"],
                            })
                    for output in _branch_equipment_outputs(effect_entry.value):
                        focus_equipment_edges.append({
                            "tag": tag, "from": focus_id, **output, "path": str(country["tree"]),
                        })

            for gate_name in ("available", "bypass", "cancel_if_invalid"):
                for gate_entry in direct_entries(body, gate_name):
                    if not isinstance(gate_entry.value, Block):
                        continue
                    for gate in _branch_idea_gates(gate_entry.value):
                        focus_idea_gate_edges.append({
                            "tag": tag, "from": focus_id, "to": gate["idea"],
                            "relation": "idea_gate", "gate": gate_name,
                            "command": gate["command"], "path": str(country["tree"]),
                            "line": gate["line"],
                        })

            for tooltip_entry in nested_entries(body, "show_ideas_tooltip"):
                target = scalar(tooltip_entry)
                if target:
                    focus_idea_gate_edges.append({
                        "tag": tag, "from": focus_id, "to": target,
                        "relation": "show_ideas_tooltip", "gate": "tooltip",
                        "command": "show_ideas_tooltip", "path": str(country["tree"]),
                        "line": tooltip_entry.line,
                    })

            for mio_id in _branch_mio_references(body):
                focus_mio_edges.append({
                    "tag": tag, "from": focus_id, "to": mio_id,
                    "relation": "uses_mio", "path": str(country["tree"]), "line": body.line,
                })

        focus_by_tag[tag] = focus_bodies
        focus_nodes_by_tag[tag] = focus_nodes

    event_file_tags = {
        str(country["events"]): tag for tag, country in countries.items()
        if country.get("events") is not None and tag in wanted
    }
    definitions_by_id = defaultdict(list)
    for item in event_report.get("metadata", []):
        definitions_by_id[item["id"]].append(item)
    defined_event_ids = set(definitions_by_id)
    references = event_report.get("references", [])
    unresolved_refs = {
        item.get("target") for item in event_report.get("unresolved_references", [])
    }

    focus_event_edges = []
    event_event_edges = []
    unresolved_local_event_edges = []
    external_event_edges = []
    for reference in references:
        target = reference.get("target")
        if not target:
            continue
        if target in defined_event_ids:
            status = "local_definition"
        elif target in unresolved_refs:
            status = "missing_in_declared_local_namespace"
        else:
            status = "external_or_unknown_namespace"
        source_kind = reference.get("source_kind")
        owner = None
        if source_kind == "focus":
            owner = next((tag for tag in wanted
                          if (reference.get("caller") or "").startswith(tag + "_")), None)
        elif source_kind == "event":
            owner = event_file_tags.get(reference.get("source"))
        edge = {
            "from_kind": source_kind, "from": reference.get("caller"),
            "to_kind": "event", "to": target, "relation": "calls_event",
            "status": status, "path": reference.get("source"), "line": reference.get("line"),
            "tag": owner,
        }
        if source_kind == "focus" and owner:
            focus_event_edges.append(edge)
        elif source_kind == "event" and owner:
            event_event_edges.append(edge)
        if source_kind in ("focus", "event") and owner in wanted:
            if status == "missing_in_declared_local_namespace":
                unresolved_local_event_edges.append(dict(edge))
            elif status == "external_or_unknown_namespace":
                external_event_edges.append(dict(edge))

    event_nodes = []
    event_idea_grant_edges = []
    event_idea_gate_edges = []
    event_equipment_edges = []
    event_edges_by_id = defaultdict(set)
    event_roots_by_focus = defaultdict(set)
    for edge in event_event_edges:
        if edge["status"] == "local_definition":
            event_edges_by_id[edge["from"]].add(edge["to"])
    for edge in focus_event_edges:
        if edge["status"] == "local_definition":
            event_roots_by_focus[edge["from"]].add(edge["to"])

    for path, parsed in event_parsed.items():
        tag = event_file_tags.get(str(path))
        if tag not in wanted:
            continue
        for kind in ("country_event", "news_event"):
            for event_entry in direct_entries(parsed.root, kind):
                if not isinstance(event_entry.value, Block):
                    continue
                body = event_entry.value
                event_id = get_scalar(body, "id")
                if not event_id:
                    continue
                event_nodes.append({
                    "tag": tag, "id": event_id, "kind": kind, "path": str(path),
                    "line": event_entry.line,
                    "is_triggered_only": (get_scalar(body, "is_triggered_only") or "").lower()
                                        in ("yes", "true", "1"),
                })
                for effect_entry in direct_entries(body, "immediate"):
                    if not isinstance(effect_entry.value, Block):
                        continue
                    for output in _branch_idea_effects(effect_entry.value):
                        if output["usage"] in ("grant", "timed_grant"):
                            event_idea_grant_edges.append({
                                "tag": tag, "from": event_id, "to": output["idea"],
                                "relation": output["usage"], "effect": "immediate",
                                "command": output["command"], "path": str(path), "line": output["line"],
                            })
                    for output in _branch_equipment_outputs(effect_entry.value):
                        event_equipment_edges.append({
                            "tag": tag, "from": event_id, **output,
                            "effect": "immediate", "path": str(path),
                        })
                for gate in _branch_idea_gates(get_block(body, "trigger")):
                    event_idea_gate_edges.append({
                        "tag": tag, "from": event_id, "to": gate["idea"],
                        "relation": "idea_gate", "gate": "event_trigger",
                        "command": gate["command"], "path": str(path), "line": gate["line"],
                    })
                for option_entry in direct_entries(body, "option"):
                    if not isinstance(option_entry.value, Block):
                        continue
                    option = option_entry.value
                    option_name = get_scalar(option, "name") or "(unnamed option)"
                    for output in _branch_idea_effects(option):
                        if output["usage"] in ("grant", "timed_grant"):
                            event_idea_grant_edges.append({
                                "tag": tag, "from": event_id, "to": output["idea"],
                                "relation": output["usage"], "effect": "option",
                                "option": option_name, "command": output["command"],
                                "path": str(path), "line": output["line"],
                            })
                    for output in _branch_equipment_outputs(option):
                        event_equipment_edges.append({
                            "tag": tag, "from": event_id, **output,
                            "effect": "option", "option": option_name, "path": str(path),
                        })
                    for gate in _branch_idea_gates(get_block(option, "trigger")):
                        event_idea_gate_edges.append({
                            "tag": tag, "from": event_id, "to": gate["idea"],
                            "relation": "idea_gate", "gate": "option_trigger",
                            "option": option_name, "command": gate["command"],
                            "path": str(path), "line": gate["line"],
                        })

    idea_definitions = idea_report.get("idea_definitions", [])
    local_idea_ids = {item["id"] for item in idea_definitions}
    all_grant_sources = defaultdict(list)
    for edge in focus_idea_grant_edges:
        all_grant_sources[edge["to"]].append({
            "kind": "focus", "id": edge["from"], "tag": edge["tag"],
            "path": edge["path"], "line": edge["line"],
        })
    for edge in event_idea_grant_edges:
        all_grant_sources[edge["to"]].append({
            "kind": "event", "id": edge["from"], "tag": edge["tag"],
            "path": edge["path"], "line": edge["line"],
        })
    known_focus_paths = {str(country["tree"]) for tag, country in countries.items() if tag in wanted}
    known_event_paths = set(event_file_tags)
    for reference in idea_report.get("idea_references", []):
        if reference.get("usage") not in ("add", "timed_add"):
            continue
        idea_id = reference.get("idea")
        if not idea_id:
            continue
        path = reference.get("path", "")
        if path in known_focus_paths or path in known_event_paths:
            continue
        match = re.match(r"^([A-Z]{3})_", idea_id)
        owner_tag = match.group(1) if match else None
        if owner_tag in wanted:
            all_grant_sources[idea_id].append({
                "kind": "other_local_source", "id": path, "tag": owner_tag,
                "path": path, "line": reference.get("line"),
            })

    def reachable_events_from_focus_ancestors(tag, focus_id):
        bodies = focus_by_tag.get(tag, {})
        ancestors = set()
        pending = list(focus_prerequisite_ids(bodies[focus_id])) if focus_id in bodies else []
        while pending:
            current = pending.pop()
            if current in ancestors:
                continue
            ancestors.add(current)
            if current in bodies:
                pending.extend(focus_prerequisite_ids(bodies[current]))
        roots = set()
        for ancestor in ancestors:
            roots.update(event_roots_by_focus.get(ancestor, ()))
        reachable = set()
        queue = list(roots)
        while queue:
            current = queue.pop()
            if current in reachable:
                continue
            reachable.add(current)
            queue.extend(event_edges_by_id.get(current, ()))
        return ancestors, reachable

    focus_idea_gate_review_candidates = []
    for edge in focus_idea_gate_edges:
        if (edge["relation"] != "idea_gate" or edge.get("gate") != "available"
                or edge["to"] not in local_idea_ids):
            continue
        tag, focus_id, idea_id = edge["tag"], edge["from"], edge["to"]
        ancestors, reachable_events = reachable_events_from_focus_ancestors(tag, focus_id)
        writers = all_grant_sources.get(idea_id, [])
        connected_writers = [
            item for item in writers
            if (item["kind"] == "focus" and item["id"] in ancestors)
            or (item["kind"] == "event" and item["id"] in reachable_events)
        ]
        if connected_writers:
            edge["upstream_grant_sources"] = connected_writers
            edge["path_status"] = "local_upstream_grant_found"
        else:
            edge["upstream_grant_sources"] = []
            edge["path_status"] = (
                "local_writer_exists_but_path_not_proven" if writers
                else "no_local_writer_found_external_or_runtime_possible"
            )
            focus_idea_gate_review_candidates.append({
                "tag": tag, "focus": focus_id, "idea": idea_id,
                "status": edge["path_status"], "path": edge["path"], "line": edge["line"],
                "known_local_writers": writers[:10],
                "reason": (
                    "A local definition and focus availability gate exist, but no grant was found "
                    "in a prerequisite ancestor or in an event called by such an ancestor. "
                    "Check alternate paths, history, decisions, on_actions, scripted effects and base MD."
                ),
            })

    idea_tooltip_edges = []
    tooltip_script_review_candidates = []
    scripted_defs = content_indexes.get("scripted_defs", {})
    scripted_by_name = {
        item["name"]: item
        for items in scripted_defs.values()
        for item in items
    }
    bracket_ref_re = re.compile(r"\[([A-Za-z_][A-Za-z0-9_]*)\]")
    for idea in idea_definitions:
        tag = idea.get("owner_tag")
        if tag not in wanted:
            continue
        for tooltip_key in idea.get("custom_modifier_tooltips", []):
            idea_tooltip_edges.append({
                "tag": tag, "from": idea["id"], "to": tooltip_key,
                "relation": "custom_modifier_tooltip",
                "path": idea["path"], "line": idea["line"],
            })
            value = get_loc_value(loc_index, tooltip_key)
            if value is None:
                continue
            for script_name in bracket_ref_re.findall(value):
                if script_name in scripted_by_name:
                    script = scripted_by_name[script_name]
                    idea_tooltip_edges.append({
                        "tag": tag, "from": tooltip_key, "to": script_name,
                        "relation": "localisation_calls_scripted_localisation",
                        "path": script["path"],
                    })
                    for idea_ref in script.get("idea_refs", []):
                        idea_tooltip_edges.append({
                            "tag": tag, "from": script_name, "to": idea_ref,
                            "relation": "scripted_localisation_checks_idea",
                            "path": script["path"],
                        })
                elif script_name.startswith(tag + "_"):
                    tooltip_script_review_candidates.append({
                        "tag": tag, "idea": idea["id"], "tooltip_key": tooltip_key,
                        "scripted_localisation": script_name,
                        "status": "local_scripted_localisation_not_found_candidate",
                        "path": idea["path"], "line": idea["line"],
                    })

    idea_stage_edges = []
    for edge in idea_report.get("stage_name_links", []):
        owner_tag = next((item["owner_tag"] for item in idea_definitions
                          if item["id"] == edge["idea"]), None)
        if owner_tag in wanted:
            idea_stage_edges.append({
                "tag": owner_tag, "from": edge["idea"], "to": edge["base_idea"],
                "relation": "stage_uses_base_name", "path": edge["path"], "line": edge["line"],
            })

    mio_visibility_edges = []
    for mio in industry_report.get("mio_definitions", []):
        if mio.get("owner_tag") not in wanted:
            continue
        for focus_id in mio.get("visible_focus_refs", []):
            mio_visibility_edges.append({
                "tag": mio["owner_tag"], "from": mio["id"], "to": focus_id,
                "relation": "visible_after_focus", "path": mio["path"], "line": mio["line"],
                "status": "local_focus" if focus_id in focus_lookup else "focus_not_found_candidate",
            })

    state_handoff_edges = []
    for link in state_flow_report.get("decision_event_state_links", []):
        if link.get("local_tag") not in wanted:
            continue
        writer, reader = link.get("writer", {}), link.get("reader", {})
        state_handoff_edges.append({
            "tag": link["local_tag"],
            "from_kind": writer.get("object_kind"), "from": writer.get("object_id"),
            "to_kind": reader.get("object_kind"), "to": reader.get("object_id"),
            "relation": "state_handoff", "state_family": link.get("family"),
            "state_id": link.get("id"), "status": link.get("status"),
            "scope_match": link.get("scope_match"), "writer": writer, "reader": reader,
        })

    local_unresolved_event_calls = [
        item for item in unresolved_local_event_edges if item.get("tag") in wanted
    ]
    external_calls = [item for item in external_event_edges if item.get("tag") in wanted]
    orphan_events = []
    for item in event_report.get("unreachable_triggered_events", []):
        tag = event_file_tags.get(item.get("path", ""))
        if tag in wanted:
            orphan_events.append({**item, "tag": tag, "status": "no_local_incoming_call_candidate"})

    by_country = {}
    for tag in sorted(wanted):
        by_country[tag] = {
            "focus_nodes": focus_nodes_by_tag.get(tag, []),
            "focus_prerequisite_edges": [x for x in focus_prerequisite_edges if x["tag"] == tag],
            "focus_event_edges": [x for x in focus_event_edges if x.get("tag") == tag],
            "focus_idea_grant_edges": [x for x in focus_idea_grant_edges if x["tag"] == tag],
            "focus_idea_gate_edges": [x for x in focus_idea_gate_edges if x["tag"] == tag],
            "focus_equipment_edges": [x for x in focus_equipment_edges if x["tag"] == tag],
            "focus_mio_edges": [x for x in focus_mio_edges if x["tag"] == tag],
            "event_nodes": [x for x in event_nodes if x["tag"] == tag],
            "event_event_edges": [x for x in event_event_edges if x.get("tag") == tag],
            "event_idea_grant_edges": [x for x in event_idea_grant_edges if x["tag"] == tag],
            "event_idea_gate_edges": [x for x in event_idea_gate_edges if x["tag"] == tag],
            "event_equipment_edges": [x for x in event_equipment_edges if x["tag"] == tag],
            "idea_tooltip_edges": [x for x in idea_tooltip_edges if x["tag"] == tag],
            "idea_stage_edges": [x for x in idea_stage_edges if x["tag"] == tag],
            "mio_visibility_edges": [x for x in mio_visibility_edges if x["tag"] == tag],
            "state_handoff_edges": [x for x in state_handoff_edges if x["tag"] == tag],
            "review_candidates": {
                "focus_idea_gate_paths": [x for x in focus_idea_gate_review_candidates if x["tag"] == tag],
                "tooltip_script_resolution": [x for x in tooltip_script_review_candidates if x["tag"] == tag],
                "unresolved_local_event_calls": [x for x in local_unresolved_event_calls if x["tag"] == tag],
                "external_event_calls": [x for x in external_calls if x["tag"] == tag],
                "unreachable_triggered_events": [x for x in orphan_events if x["tag"] == tag],
                "mio_visibility_focus": [x for x in mio_visibility_edges
                                         if x["tag"] == tag and x["status"] != "local_focus"],
            },
        }

    return {
        "scope": "local_static_cross_reference",
        "limits": (
            "Edges record explicit local references. Focus prerequisite ancestry is a conservative union "
            "of referenced focus IDs; dynamic scopes, external base-MD writers, indirect scripted calls, "
            "AI/runtime timing and option probabilities are not simulated. Review candidates never affect exit code."
        ),
        "counts": {
            "focus_nodes": sum(len(item["focus_nodes"]) for item in by_country.values()),
            "focus_prerequisite_edges": len(focus_prerequisite_edges),
            "focus_event_edges": len(focus_event_edges),
            "event_event_edges": len(event_event_edges),
            "focus_idea_grant_edges": len(focus_idea_grant_edges),
            "focus_idea_gate_edges": len(focus_idea_gate_edges),
            "event_idea_grant_edges": len(event_idea_grant_edges),
            "event_idea_gate_edges": len(event_idea_gate_edges),
            "idea_tooltip_edges": len(idea_tooltip_edges),
            "idea_stage_edges": len(idea_stage_edges),
            "focus_mio_edges": len(focus_mio_edges),
            "mio_visibility_edges": len(mio_visibility_edges),
            "state_handoff_edges": len(state_handoff_edges),
            "review_candidates": (
                len(focus_idea_gate_review_candidates) + len(tooltip_script_review_candidates)
                + len(local_unresolved_event_calls) + len(external_calls) + len(orphan_events)
                + sum(1 for item in mio_visibility_edges if item["status"] != "local_focus")
            ),
        },
        "by_country": by_country,
        "review_candidates": {
            "focus_idea_gate_paths": focus_idea_gate_review_candidates,
            "tooltip_script_resolution": tooltip_script_review_candidates,
            "unresolved_local_event_calls": local_unresolved_event_calls,
            "external_event_calls": external_calls,
            "unreachable_triggered_events": orphan_events,
        },
    }


ERRORS = [
    "parse_errors", "dup_focus_ids", "log_mismatch", "no_log", "prereq_missing",
    "mutex_missing", "relpos_missing", "title_missing", "desc_missing", "dup_loc_keys",
    "scripted_loc_duplicate", "swap_same_idea", "event_not_found",
    "event_option_label_missing", "event_option_no_log",
    "event_title_key_missing", "event_desc_key_missing",
]
WARNS = [
    "empty_reward", "nonstandard_filter", "hidden_branch_focus", "event_external",
    "tech_bonus_no_uses", "title_gt30", "desc_lt150", "desc_gt340", "banned_phrase",
    "tooltip_only_reward", "event_generic_label", "event_label_gt35", "event_option_label_external",
    "foreign_tag_ref", "idea_not_found",
    "scripted_loc_missing", "scripted_loc_loc_missing", "scripted_loc_idea_missing", "scripted_loc_unused",
    "event_title_key_external", "event_desc_key_external",
]

INFOS = ["event_without_picture"]


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Статический аудит HOI4/TDF country content")
    ap.add_argument("repo", nargs="?", default=".", help="корень репозитория (по умолчанию текущая папка)")
    ap.add_argument("--tags", help="список тегов через запятую, например POR,KAZ")
    ap.add_argument("--details", help="показать подробности проверок одной страны")
    ap.add_argument("--json", metavar="PATH", help="сохранить полный отчёт в UTF-8 JSON")
    ap.add_argument(
        "--require-external-registry", action="store_true",
        help="завершиться с ошибкой, если реестр внешних зависимостей отсутствует",
    )
    args = ap.parse_args(argv)

    try:
        countries, loc_index = discover(args.repo)
        all_focus, defined_events, defined_namespaces, event_parsed = build_global_indexes(countries, args.repo)
        content_indexes = build_content_indexes(args.repo, countries, loc_index)
        idea_report = build_idea_lifecycle_audit(args.repo, countries, loc_index, content_indexes, event_parsed)
        event_report = build_event_audit(args.repo, countries, loc_index, event_parsed, content_indexes)
        decision_report = build_decision_audit(args.repo, countries, loc_index, all_focus, defined_events,
                                               defined_namespaces, event_parsed, content_indexes)
        industry_report = build_industry_audit(args.repo, countries, loc_index, all_focus, event_parsed)
        state_flow_report = build_state_flow_audit(args.repo, countries, event_parsed)
        external_dependency_report = build_external_dependency_audit(
            args.repo, event_report, decision_report, idea_report, industry_report, state_flow_report
        )
        if args.require_external_registry and not external_dependency_report.get("registry_available"):
            raise AuditInputError(
                "обязательный реестр внешних зависимостей не найден: {}".format(
                    external_dependency_report.get("registry_path", "docs/research/external-dependencies.json")
                )
            )
        wanted = [part.strip().upper() for part in args.tags.split(",") if part.strip()] if args.tags else sorted(countries)
        unknown = sorted(set(wanted) - set(countries))
        if unknown:
            ap.error("не найдены теги: {}. Доступны: {}".format(", ".join(unknown), ", ".join(sorted(countries))))
        if args.details and args.details.upper() not in wanted:
            ap.error("--details {} не входит в проверяемый набор тегов".format(args.details.upper()))
        results = {
            tag: audit_country(tag, countries[tag], loc_index, all_focus, set(countries), defined_events,
                               defined_namespaces, event_parsed, content_indexes)
            for tag in wanted
        }
        branch_connectivity_report = build_branch_connectivity_audit(
            countries, event_report, idea_report, industry_report, state_flow_report,
            event_parsed, content_indexes, loc_index, tags=wanted,
        )

        columns = ["n_focus", "desc_median"] + ERRORS + WARNS + ["space_indent_lines", "brace_balance"]
        short = lambda name: name.replace("_", " ")[:11]
        print("\t".join(["tag"] + [short(col) for col in columns]))
        for tag, result in results.items():
            row = [tag]
            for key in columns:
                value = result.get(key, 0)
                row.append(str(len(value)) if isinstance(value, list) else str(value))
            print("\t".join(row))
        print("\nERROR-проверки: " + ", ".join(ERRORS) + "\nWARN-проверки: " + ", ".join(WARNS))
        print("event_not_found — ссылка на ID в namespace, который объявлен в срезе, но не содержит такое событие.")
        print("event_external — namespace не найден в срезе; ссылка может принадлежать базовому моду.")
        print("\nГлобальный аудит событий: {} определений (country_event {}, news_event {}), {} namespace.".format(
            event_report["counts"]["definitions"], event_report["counts"]["country_event"],
            event_report["counts"]["news_event"], event_report["counts"]["namespaces"]))
        print("\nАудит решений: {} файлов, {} категорий, {} решений.".format(
            decision_report["counts"]["files"], decision_report["counts"]["categories"],
            decision_report["counts"]["decisions"]))
        for key in ("parse_errors", "duplicate_category_ids", "duplicate_decision_ids",
                    "missing_category_localisation", "missing_decision_localisation",
                    "duplicate_localisation_definitions", "missing_tooltip_localisation",
                    "external_tooltip_localisation", "missing_decision_references",
                    "external_decision_references", "missing_focus_references",
                    "external_focus_references", "missing_event_references",
                    "external_event_references", "idea_reference_candidates",
                    "flag_reference_candidates", "missing_scripted_localisation",
                    "invalid_numeric_fields", "custom_cost_pair_issues", "custom_cost_conflicts",
                    "custom_cost_without_debit", "repeatability_warnings",
                    "empty_effect_warnings", "condition_review_candidates",
                    "nonnumeric_highlight_states", "unknown_highlight_states"):
            print("  decision {}: {}".format(key, len(decision_report[key])))
        print("  highlight states: {}, local state inventory available: {}".format(
            len(decision_report["highlight_state_references"]), decision_report["state_inventory_available"]))

        print("\nАудит MIO/техники: {} MIO-файлов, {} организаций, {} ссылок; {} equipment IDs, {} модулей, {} технологий; {} вариантов и {} выдач техники.".format(
            industry_report["counts"]["mio_files"], industry_report["counts"]["mio_definitions"],
            industry_report["counts"]["mio_references"], industry_report["counts"]["equipment_ids"],
            industry_report["counts"]["module_ids"], industry_report["counts"]["technology_ids"],
            industry_report["counts"]["equipment_variants"], industry_report["counts"]["stockpile_grants"]))
        for key in ("mio_parse_errors", "equipment_parse_errors", "module_parse_errors",
                    "technology_parse_errors", "duplicate_mio_ids", "missing_local_mio_references",
                    "external_mio_references", "missing_local_mio_name_localisation",
                    "external_mio_name_localisation_candidates", "mio_name_matches_other_mio",
                    "local_mio_visibility_focus_candidates", "duplicate_equipment_ids",
                    "unknown_equipment_type_references", "unknown_module_references",
                    "unknown_technology_references",
                    "invalid_stockpile_amounts", "local_equipment_localisation_candidates"):
            print("  industry {}: {}".format(key, len(industry_report[key])))

        print("\nВнешние зависимости: {} кандидатов; зарегистрировано {}, без записи в реестре {}; baseline {} @ {}.".format(
            external_dependency_report["counts"]["findings"],
            external_dependency_report["counts"]["registered_findings"],
            external_dependency_report["counts"]["unregistered"],
            external_dependency_report.get("baseline", {}).get("repository", "unknown"),
            external_dependency_report.get("baseline", {}).get("commit", "unknown")))
        print("\nАудит межфайлового состояния: {} файлов; {} history; {} scripted effects / {} calls; {} scripted triggers / {} calls; {} on_actions; {} flags, {} variables, {} arrays.".format(
            state_flow_report["counts"]["source_files"], state_flow_report["counts"]["history_files"],
            state_flow_report["counts"]["scripted_effect_definitions"], state_flow_report["counts"]["scripted_effect_calls"],
            state_flow_report["counts"]["scripted_trigger_definitions"], state_flow_report["counts"]["scripted_trigger_calls"],
            state_flow_report["counts"]["on_action_hooks"], state_flow_report["counts"]["flag_symbols"],
            state_flow_report["counts"]["variable_symbols"], state_flow_report["counts"]["array_symbols"]))
        print("  decision/event state links: {}".format(state_flow_report["counts"]["decision_event_state_links"]))
        for key in ("parse_errors", "script_parse_errors", "duplicate_scripted_effect_definitions",
                    "duplicate_scripted_trigger_definitions", "scripted_effects_without_local_call",
                    "scripted_triggers_without_local_call", "unresolved_scripted_call_candidates",
                    "potentially_unread_local_flags", "local_flags_read_without_writer",
                    "potentially_unread_local_variables", "local_variables_read_without_writer",
                    "potentially_unread_local_arrays", "local_arrays_read_without_writer",
                    "idea_on_add_without_matching_on_remove", "countries_without_local_history"):
            print("  state_flow {}: {}".format(key, len(state_flow_report[key])))
        print("  on_action inventory available: {}; scripted-trigger inventory available: {}; history inventory available: {}".format(
            state_flow_report["on_action_inventory_available"],
            state_flow_report["scripted_trigger_inventory_available"],
            state_flow_report["history_inventory_available"]))

        for key in ("parse_errors", "missing_event_ids", "missing_title_fields", "missing_desc_fields",
                    "missing_option_names", "duplicate_event_ids", "duplicate_namespaces",
                    "missing_localisation", "external_localisation", "duplicate_localisation_definitions",
                    "missing_option_localisation", "external_option_localisation", "generic_option_labels",
                    "long_option_labels", "options_without_log", "missing_event_idea_candidates",
                    "missing_event_scripted_localisation", "reused_title_desc_keys",
                    "unresolved_references", "external_references", "scripted_effect_references",
                    "unreachable_triggered_events",
                    "events_without_picture"):
            print("  {}: {}".format(key, len(event_report[key])))

        branch_counts = branch_connectivity_report["counts"]
        print("\nСвязность веток: {} focus, {} prerequisite, {} focus→event, {} event→event, {} focus→idea, {} event→idea, {} idea-tooltip, {} state handoff; {} review candidates.".format(
            branch_counts["focus_nodes"], branch_counts["focus_prerequisite_edges"],
            branch_counts["focus_event_edges"], branch_counts["event_event_edges"],
            branch_counts["focus_idea_grant_edges"] + branch_counts["focus_idea_gate_edges"],
            branch_counts["event_idea_grant_edges"], branch_counts["idea_tooltip_edges"],
            branch_counts["state_handoff_edges"], branch_counts["review_candidates"]))
        print("\nАудит нацдухов: {} файлов, {} идей (видимых {}, скрытых {}), {} ссылок.".format(
            idea_report["counts"]["idea_files"], idea_report["counts"]["definitions"],
            idea_report["counts"]["visible_ideas"], idea_report["counts"]["hidden_ideas"],
            idea_report["counts"]["idea_references"]))
        for key in ("parse_errors", "source_parse_errors", "duplicate_idea_ids", "missing_name_localisation",
                    "missing_local_idea_references", "external_idea_references",
                    "unresolved_unprefixed_idea_references", "not_locally_granted_candidates",
                    "custom_modifier_tooltip_missing_localisation",
                    "custom_modifier_tooltip_scripted_loc_candidates",
                    "custom_modifier_tooltip_static_key_candidates"):
            print("  ideas {}: {}".format(key, len(idea_report[key])))

        if args.details:
            tag = args.details.upper()
            result = results[tag]
            for key in ERRORS + WARNS + INFOS:
                if result.get(key):
                    print("\n[{}] {}".format(key, len(result[key])))
                    for item in result[key][:60]:
                        print("  ", item)
            flow = branch_connectivity_report.get("by_country", {}).get(tag, {})
            for key, items in flow.get("review_candidates", {}).items():
                if items:
                    print("\n[branch_connectivity:{}] {}".format(key, len(items)))
                    for item in items[:60]:
                        print("  ", item)

        if args.json:
            report_data = dict(results)
            report_data["_events"] = event_report
            report_data["_decisions"] = decision_report
            report_data["_industry"] = industry_report
            report_data["_ideas"] = idea_report
            report_data["_state_flow"] = state_flow_report
            report_data["_external_dependencies"] = external_dependency_report
            report_data["_branch_connectivity"] = branch_connectivity_report
            with open(args.json, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(report_data, handle, ensure_ascii=False, indent=2)
                handle.write("\n")

        content_index_script_errors = [
            error
            for errors in content_indexes.get("script_parse_errors", {}).values()
            for error in errors
        ]
        registry_errors = (
            external_dependency_report.get("registry_available", False)
            and bool(external_dependency_report.get("registry_validation_issues"))
        )
        has_errors = any(result.get(key) for result in results.values() for key in ERRORS)
        has_errors = has_errors or reports_have_parse_errors(
            idea_report, event_report, decision_report, industry_report, state_flow_report,
            {"script_parse_errors": content_index_script_errors},
        ) or registry_errors
        has_errors = has_errors or bool(
            event_report["missing_event_ids"]
            or event_report["duplicate_event_ids"]
            or event_report["unresolved_references"]
            or event_report["missing_localisation"]
            or event_report["missing_option_localisation"]
            or event_report["missing_title_fields"]
            or event_report["missing_desc_fields"]
            or event_report["missing_option_names"]
            or event_report["options_without_log"]
        )
        same_file_category_duplicates = any(
            item["scope"] == "same_file" for item in decision_report["duplicate_category_ids"]
        )
        has_errors = has_errors or bool(same_file_category_duplicates
                                         or decision_report["duplicate_decision_ids"]
                                         or decision_report["missing_category_localisation"]
                                         or decision_report["missing_decision_localisation"]
                                         or decision_report["invalid_numeric_fields"]
                                         or decision_report["missing_decision_references"]
                                         or decision_report["missing_focus_references"]
                                         or decision_report["missing_event_references"])
        return 1 if has_errors else 0
    except AuditInputError as exc:
        print("ОШИБКА: {}".format(exc), file=sys.stderr)
        return 2
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print("ОШИБКА чтения входных данных / JSON: {}".format(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
