"""Построение результата аудита одной страны.

Часть пакета tdf_audit_lib; публичный вход: scripts/tdf_audit.py.
"""
import re
import statistics as st
from collections import Counter, defaultdict
from .core import (
    BANNED,
    BANNED_WORD,
    Block,
    GENERIC_LABELS,
    Token,
    direct_entries,
    find_named_blocks,
    get_block,
    get_scalar,
    iter_event_calls,
    nested_entries,
    scalar,
    walk_entries,
)
from .events import (
    is_local_event_key,
)
from .indexes import (
    focus_prerequisite_ids,
    get_loc_value,
    has_disabled_allow_branch,
    idea_candidates,
)


def audit_country(tag, country, loc_index, all_focus, known_tags, defined_events, defined_namespaces, event_parsed, content_indexes):
    source = country["tree_source"]
    parsed = country["tree_parsed"]
    R = defaultdict(list)
    R["space_indent_lines"] = sum(1 for line in source.splitlines() if re.match(r"^ +\S", line))
    R["brace_balance"] = parsed.brace_balance
    for issue in parsed.issues:
        R["parse_errors"].append("{}:{}".format(country["tree"].name, issue))

    duplicate_keys = []
    identical_duplicate_keys = []
    for key, occurrences in loc_index.items():
        if len(occurrences) < 2 or not key.startswith(tag + "_"):
            continue
        values = {occurrence.value for occurrence in occurrences}
        if len(values) == 1:
            identical_duplicate_keys.append(key)
        else:
            duplicate_keys.append(key)
    R["dup_loc_keys"] = sorted(duplicate_keys)
    R["dup_loc_keys_identical"] = sorted(identical_duplicate_keys)
    for issue in content_indexes["script_parse_errors"].get(tag, []):
        R["parse_errors"].append(issue)

    defined_ideas = content_indexes["idea_ids"].get(tag, set())

    definitions = content_indexes["scripted_defs"].get(tag, [])
    definitions_by_name = defaultdict(list)
    for definition in definitions:
        definitions_by_name[definition["name"]].append(definition)
    R["scripted_loc_duplicate"] = sorted(
        name for name, items in definitions_by_name.items()
        if len(items) > 1 and len({item.get("signature") for item in items}) > 1
    )
    R["scripted_loc_duplicate_identical"] = sorted(
        name for name, items in definitions_by_name.items()
        if len(items) > 1 and len({item.get("signature") for item in items}) == 1
    )
    defined_scripted_names = set(definitions_by_name)
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
