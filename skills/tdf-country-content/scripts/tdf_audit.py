#!/usr/bin/env python3
"""Статический аудит контента стран TDF/MDC по правилам tdf-country-content.

Запуск из корня репозитория:
    python3 -I skills/tdf-country-content/scripts/tdf_audit.py .
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
                self.issues.append(ParseIssue(token.line, token.column, "блок без имени"))
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
    for path in sorted(nf.glob("*_Focus_Tree.txt")):
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
            "events": event_files_by_stem.get(stem.lower()),
        }
    if not countries:
        raise AuditInputError("не удалось обнаружить ни одного *_Focus_Tree.txt с тегом страны в {}".format(nf))
    return countries, loc_index


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

    return {
        "idea_ids": idea_ids,
        "scripted_defs": scripted_defs,
        "scripted_refs": scripted_refs,
        "script_parse_errors": script_parse_errors,
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
    """Yield static event calls in both scalar and block syntax."""
    for entry in walk_entries(block):
        if entry.key.value not in EVENT_CALL_KEYS:
            continue
        event_id = entry.value.value if isinstance(entry.value, Token) else get_scalar(entry.value, "id")
        if event_id:
            yield entry.key.value, event_id, entry.line


def is_local_event_key(key: str, event_id: str, tag: Optional[str] = None) -> bool:
    """Recognize event-local keys without treating shared/base keys as local."""
    namespace = event_id.split(".", 1)[0] if "." in event_id else ""
    if namespace and (key == namespace or key.startswith(namespace + ".") or key.startswith(namespace + "_")):
        return True
    return bool(tag and key.startswith(tag + "_"))


def build_event_audit(repo, countries, loc_index, event_parsed):
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
                continue
            if key not in loc_index:
                item = {"key": key, "event_id": definition["id"],
                        "path": definition["path"], "line": option_entry.line}
                (missing_option_loc if is_local_event_key(key, definition["id"], tag) else external_option_loc).append(item)

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
        for path in iter_files(source_dir, ".txt"):
            parsed = parse_hoi(read(path))
            add_references(parsed.root, source_kind, path, path.stem)

    for definition in definitions:
        add_references(definition["block"], "event", definition["path"], definition["id"])

    defined_ids = set(definitions_by_id)
    defined_namespaces = {item["namespace"] for item in namespace_declarations}
    unresolved_references, external_references = [], []
    event_edges = defaultdict(set)
    root_events = set()
    for reference in references:
        target = reference["target"]
        if target in defined_ids:
            if reference["source_kind"] == "event":
                event_edges[reference["caller"]].add(target)
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
        if definition["is_triggered_only"] and definition["id"] not in reachable:
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
        "reused_title_desc_keys": reused_event_loc, "unresolved_references": unresolved_references,
        "external_references": external_references, "unreachable_triggered_events": orphan_triggered,
        "events_without_picture": missing_picture, "metadata": metadata,
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
    args = ap.parse_args(argv)

    try:
        countries, loc_index = discover(args.repo)
        all_focus, defined_events, defined_namespaces, event_parsed = build_global_indexes(countries, args.repo)
        content_indexes = build_content_indexes(args.repo, countries, loc_index)
        event_report = build_event_audit(args.repo, countries, loc_index, event_parsed)
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
        for key in ("parse_errors", "missing_event_ids", "missing_title_fields", "missing_desc_fields",
                    "missing_option_names", "duplicate_event_ids", "duplicate_namespaces",
                    "missing_localisation", "external_localisation", "duplicate_localisation_definitions",
                    "missing_option_localisation", "external_option_localisation", "reused_title_desc_keys",
                    "unresolved_references", "external_references", "unreachable_triggered_events",
                    "events_without_picture"):
            print("  {}: {}".format(key, len(event_report[key])))

        if args.details:
            tag = args.details.upper()
            result = results[tag]
            for key in ERRORS + WARNS + INFOS:
                if result.get(key):
                    print("\n[{}] {}".format(key, len(result[key])))
                    for item in result[key][:60]:
                        print("  ", item)

        if args.json:
            report_data = dict(results)
            report_data["_events"] = event_report
            with open(args.json, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(report_data, handle, ensure_ascii=False, indent=2)
                handle.write("\n")

        has_errors = any(result.get(key) for result in results.values() for key in ERRORS)
        has_errors = has_errors or bool(event_report["parse_errors"] or event_report["missing_event_ids"]
                                         or event_report["duplicate_event_ids"] or event_report["unresolved_references"]
                                         or event_report["missing_localisation"] or event_report["missing_option_localisation"])
        return 1 if has_errors else 0
    except AuditInputError as exc:
        print("ОШИБКА: {}".format(exc), file=sys.stderr)
        return 2
    except OSError as exc:
        print("ОШИБКА ввода-вывода: {}".format(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
