"""Обнаружение тегов и построение индексов контента (идеи, локализация, глобальные индексы).

Часть пакета tdf_audit_lib; публичный вход: scripts/tdf_audit.py.
"""
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Union
from .core import (
    AuditInputError,
    Block,
    Entry,
    LOC_LINE_RE,
    LocEntry,
    ParseResult,
    TAG_RE,
    Token,
    _structural_signature,
    direct_entries,
    find_named_blocks,
    get_block,
    get_scalar,
    iter_event_calls,
    iter_files,
    nested_entries,
    parse_hoi,
    read,
    scalar,
    walk_entries,
)


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
            for group_entry in ideas_block.entries:
                if not isinstance(group_entry.value, Block):
                    continue
                group_name = group_entry.key.value
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
                "lifecycle_event_calls": [
                    {"lifecycle": lifecycle, "kind": call_kind, "target": target, "line": event_line}
                    for lifecycle in ("on_add", "on_remove")
                    for lifecycle_entry in direct_entries(block, lifecycle)
                    if isinstance(lifecycle_entry.value, Block)
                    for call_kind, target, event_line in iter_event_calls(lifecycle_entry.value)
                ],
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
                "signature": _structural_signature(definition.value),
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
    for occurrences in loc_index.values():
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
