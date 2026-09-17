import json
import re
from pathlib import Path


FILE = Path(__file__).parent / "memory.json"


# Fallback template used only when memory.json is missing or
# unreadable. This is a SNAPSHOT of real personal data as of
# when it was last set -- if memory.json is ever lost, IRIS
# will regenerate from exactly this, frozen at this point in
# time (not necessarily your current, most up-to-date state).
DEFAULT = {
    "user": {
        "name": "Admin"
    },
    "assistant": {
        "name": "IRIS",
        "full_form": "Information Reasoning Interaction System",
        "purpose": (
            "A personal AI assistant designed to understand the user, "
            "remember what matters, help solve problems, manage tasks, "
            "and make everyday life easier."
        )
    },
    "preferences": {
        "short_answers": "short answers"
    },
    "learning": [
        "Linux"
    ],
    "personal": {
        "favorite_colour": "violet",
        "favorite_movie": "Iron Man",
        "favorite_food": [
            "biriyani",
            "shwarma"
        ],
        "personal_email": "elvinjoy88@gmail.com",
        "work_email": "elvin@ergonomics-me.com",
        "phone_numbers": {
            "india": "+91 8129808383",
            "uae": "+971 56 714 6689"
        }
    },
    "family": {
        "mother": {
            "name": "Nicy Antony"
        },
        "sister": {
            "name": "Emerin Joy"
        },
        "father": {
            "name": "joy paul"
        }
    },
    "pets": [
        {
            "name": "Puffy",
            "breed": "Pomeranian",
            "colour": "white"
        }
    ],
    "work": {
        "role": "Technical Support Assistant",
        "location": "Dubai",
        "work_email": "elvin@ergonomics-me.com",
        "company_address": "1614 Parklane Tower, Business Bay, Dubai"
    },
    "facts": [
        "my fav movie is iron man"
    ],
    "hobbies": {
        "listening_to_music_and_playing_games": "listening to music and playing games"
    }
}


def load():
    if not FILE.exists():
        save(DEFAULT)
        return DEFAULT.copy()
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except Exception:
        return DEFAULT.copy()


def save(data):
    """Atomic write: write to a temp file first, then replace the
    real file. Prevents a crash mid-write from corrupting or
    truncating memory.json."""
    tmp = FILE.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(data, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )
    tmp.replace(FILE)


def get_user_name():
    return load().get("user", {}).get("name")


def get_assistant_info():
    return load().get("assistant", DEFAULT["assistant"])


def _normalize_key(text):
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "preference"


def _split_key_value(text):
    m = re.match(r"^([A-Za-z0-9 _\-]{2,40}):\s*(.+)$", text.strip())
    if m:
        return _normalize_key(m.group(1)), m.group(2).strip()
    return _normalize_key(text), text.strip()


def _merge_fact_into_dict(entry, fact):
    """Merge a fact string into an existing dict entry: if the
    fact looks like 'key: value', set that field directly;
    otherwise file the raw sentence under a 'notes' list."""
    key, value = _split_key_value(fact)
    if ":" in fact:
        entry[key] = value
    else:
        notes = entry.setdefault("notes", [])
        if fact not in notes:
            notes.append(fact)


def add_memory(category, fact, subject=None):
    """Create/append. (Create)"""
    data = load()
    fact = str(fact).strip()
    subject = str(subject).strip() if subject else None
    if not fact:
        return

    category = (category or "fact").strip().lower()

    # -------------------------------------------------------
    # FIXED CATEGORIES (unchanged behaviour)
    # -------------------------------------------------------

    if category == "name":
        data.setdefault("user", {})["name"] = fact

    elif category == "preference":
        preferences = data.setdefault("preferences", {})
        if isinstance(preferences, list):
            migrated = {}
            for item in preferences:
                k, v = _split_key_value(item)
                migrated[k] = v
            preferences = migrated
            data["preferences"] = preferences

        key, value = _split_key_value(fact)
        preferences[key] = value

    elif category == "learning":
        learning = data.setdefault("learning", [])
        if fact not in learning:
            learning.append(fact)

    elif category == "fact":
        facts = data.setdefault("facts", [])
        if fact not in facts:
            facts.append(fact)

    # -------------------------------------------------------
    # DYNAMIC / CUSTOM SECTIONS
    #
    # Any other category name is treated as its own top-level
    # section (e.g. "pets", "family", "vehicle", "hobbies").
    # Existing sections keep their current shape (list vs dict);
    # brand-new sections default to a dict keyed by subject.
    # -------------------------------------------------------

    else:
        section_key = _normalize_key(category)
        section = data.get(section_key)

        if isinstance(section, list):
            # Collection-style section (e.g. pets: list of dicts).
            if subject:
                sub_norm = _normalize_key(subject)
                match = None
                for item in section:
                    if isinstance(item, dict) and _normalize_key(str(item.get("name", ""))) == sub_norm:
                        match = item
                        break
                if match is None:
                    match = {"name": subject}
                    section.append(match)
                _merge_fact_into_dict(match, fact)
            else:
                if fact not in section:
                    section.append(fact)

        else:
            # Dict-style section (personal/family/work, or brand new).
            if not isinstance(section, dict):
                section = {}

            if subject:
                sub_norm = _normalize_key(subject)
                existing_entry = section.get(sub_norm)
                if not isinstance(existing_entry, dict):
                    existing_entry = {}
                _merge_fact_into_dict(existing_entry, fact)
                section[sub_norm] = existing_entry
            else:
                key, value = _split_key_value(fact)
                section[key] = value

            data[section_key] = section

    save(data)


def _flatten(prefix, value, lines):
    if isinstance(value, dict):
        for k, v in value.items():
            _flatten(f"{prefix}.{k}" if prefix else k, v, lines)
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, (dict, list)):
                _flatten(prefix, item, lines)
            elif item not in (None, ""):
                lines.append(f"{prefix}: {item}")
    else:
        if value not in (None, ""):
            lines.append(f"{prefix}: {value}")


def get_full_memory():
    """Return the entire raw memory dict. (Read)"""
    return load()


def _iter_leaves(data, path=""):
    """Yield (path, container, key_or_index, value) for every node in
    the memory tree, so update/delete-by-query can search dict keys,
    nested entries and list items in one pass."""
    if isinstance(data, dict):
        for k, v in data.items():
            new_path = f"{path}.{k}" if path else k
            yield (new_path, data, k, v)
            yield from _iter_leaves(v, new_path)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            new_path = f"{path}[{i}]"
            yield (new_path, data, i, item)
            yield from _iter_leaves(item, new_path)


def _norm_for_search(text):
    """Normalize text for fuzzy matching, folding common British/
    American spelling differences (colour/color, favourite/favorite,
    behaviour/behavior, ...) so 'favourite colour' and the stored key
    'favorite_colour' compare equal."""
    key = _normalize_key(text)
    key = re.sub(r"our", "or", key)
    return _apply_relation_aliases(key)


_RELATION_ALIASES = {
    "mom": "mother", "mum": "mother", "mommy": "mother", "mama": "mother",
    "dad": "father", "daddy": "father", "papa": "father",
    "bro": "brother", "sis": "sister",
}

_FAMILY_WORDS = {
    "mother", "father", "sister", "brother", "son", "daughter", "wife",
    "husband", "grandmother", "grandfather", "uncle", "aunt", "cousin",
}


def _apply_relation_aliases(normalized):
    """Fold colloquial family-relation words (mom, dads, sisters, ...)
    onto the canonical word used as the actual JSON key (mother,
    father, sister, ...), token by token."""
    tokens = normalized.split("_")
    out = []
    for t in tokens:
        if t in _RELATION_ALIASES:
            out.append(_RELATION_ALIASES[t])
            continue
        if len(t) > 3 and t.endswith("s"):
            stem = t[:-1]
            if stem in _RELATION_ALIASES:
                out.append(_RELATION_ALIASES[stem])
                continue
            if stem in _FAMILY_WORDS:
                out.append(stem)
                continue
        out.append(t)
    return "_".join(out)


def _immediate_parent_name(path):
    """Given an _iter_leaves path like 'family.mother.name', return
    the immediate parent segment ('mother'), so a generic key like
    'name' can also be matched combined with its parent as
    'mother_name'. Returns None if there's no parent segment."""
    segments = [s.rstrip("]") for s in re.split(r"\.|\[", path) if s]
    if len(segments) >= 2:
        return segments[-2]
    return None


def _composite_label(path, container, key):
    """Human-friendly label to combine with a leaf key for composite
    matching -- e.g. 'mother' for family.mother.name (a dict nested
    under a named dict key), or a named list entry's own name
    ('puffy') for pets[0].breed, so 'change puffy's breed' resolves
    correctly instead of only matching a bare 'breed' key.

    The entry's own "name" field is used for every OTHER field on
    that entry, but never for the "name" field itself -- otherwise
    "family.mother.name" would label itself with its own value
    ("nicy antony") instead of its structural parent ("mother").
    """
    if key != "name" and isinstance(container, dict) and container.get("name"):
        return _norm_for_search(str(container["name"]))
    parent = _immediate_parent_name(path)
    return _norm_for_search(parent) if parent else None


def _find_target(data, norm_query, exact_only=False):
    """Search the memory tree for the best match to norm_query.
    Tries an EXACT normalized match first across every dict key,
    named sub-entry, and list item; only if nothing matches exactly
    does it fall back to a conservative partial match (and even then,
    only against strings of a reasonable length, to avoid a short
    generic key like 'name' matching inside a longer query).
    Returns (container, key_or_index, path) or None.
    """
    # Pass 1: exact match.
    for path, container, key, value in _iter_leaves(data):
        if isinstance(container, dict):
            key_norm = _norm_for_search(str(key))
            composite = _composite_label(path, container, key)
            composite_norm = _norm_for_search(f"{composite}_{key}") if composite else None
            if key_norm == norm_query or (composite_norm and composite_norm == norm_query):
                return (container, key, path)
            if isinstance(value, dict):
                name_norm = _norm_for_search(str(value.get("name", "")))
                if name_norm and name_norm == norm_query:
                    return (container, key, path)
        elif isinstance(container, list):
            if isinstance(value, dict):
                name_norm = _norm_for_search(str(value.get("name", "")))
                if name_norm and name_norm == norm_query:
                    return (container, key, path)
            else:
                if _norm_for_search(str(value)) == norm_query:
                    return (container, key, path)

    if exact_only:
        return None

    # Pass 2: conservative partial match (length-gated to avoid a
    # short generic word swallowing an unrelated field).
    for path, container, key, value in _iter_leaves(data):
        if isinstance(value, (dict, list)):
            continue
        cand = _norm_for_search(str(key) if isinstance(container, dict) else str(value))
        if not cand:
            continue
        shorter, longer = (cand, norm_query) if len(cand) <= len(norm_query) else (norm_query, cand)
        if len(shorter) >= 5 and shorter in longer:
            return (container, key, path)

    return None


def delete_memory(category, subject=None, field=None):
    """Precise delete. (Delete)

    - category only            -> removes the whole top-level section
    - category + field         -> removes one key from a dict section
    - category + subject       -> removes one entry (list item or
                                   dict sub-entry) matching that subject
    - category + subject+field -> removes one field from that entry
    Returns True if something was actually removed, False otherwise.
    """
    data = load()
    section_key = _normalize_key(category)
    if section_key not in data:
        return False
    section = data[section_key]

    if subject:
        sub_norm = _normalize_key(subject)
        if isinstance(section, list):
            match = None
            for item in section:
                if isinstance(item, dict) and _normalize_key(str(item.get("name", ""))) == sub_norm:
                    match = item
                    break
            if match is None:
                return False
            if field:
                if field not in match:
                    return False
                del match[field]
            else:
                section.remove(match)
        elif isinstance(section, dict):
            entry = section.get(sub_norm)
            if entry is None:
                return False
            if field:
                if not isinstance(entry, dict) or field not in entry:
                    return False
                del entry[field]
            else:
                del section[sub_norm]
        else:
            return False
    elif field:
        if isinstance(section, dict) and field in section:
            del section[field]
        elif isinstance(section, list) and field in section:
            section.remove(field)
        else:
            return False
    else:
        del data[section_key]

    save(data)
    return True


def delete_by_query(query):
    """Fuzzy delete for free-text requests like 'forget my favourite
    colour' or 'delete puffy'. Returns a short path string describing
    what was removed, or None if nothing matched. (Delete)"""
    data = load()
    norm_query = _norm_for_search(query)
    if not norm_query:
        return None

    found = _find_target(data, norm_query)
    if not found:
        return None

    container, key, path = found
    del container[key]
    save(data)
    return path


def update_by_query(query, value):
    """Fuzzy update for free-text requests like 'change my favourite
    colour to green' or "change puffy's breed to spitz". Only ever
    overwrites an existing plain field (never a whole section or
    named entry, to avoid clobbering structured data). Returns a
    path string on success, or None if no matching field exists yet.
    (Update)"""
    data = load()
    norm_query = _norm_for_search(query)
    if not norm_query:
        return None

    def scan(exact_only):
        for path, container, key, val in _iter_leaves(data):
            if not isinstance(container, dict) or isinstance(val, (dict, list)):
                continue
            key_norm = _norm_for_search(str(key))
            composite = _composite_label(path, container, key)
            composite_norm = _norm_for_search(f"{composite}_{key}") if composite else None
            if key_norm == norm_query or (composite_norm and composite_norm == norm_query):
                return (container, key, path)
            if not exact_only:
                shorter, longer = (key_norm, norm_query) if len(key_norm) <= len(norm_query) else (norm_query, key_norm)
                if len(shorter) >= 5 and shorter in longer:
                    return (container, key, path)
        return None

    found = scan(exact_only=True) or scan(exact_only=False)
    if not found:
        return None

    container, key, path = found
    container[key] = value
    save(data)
    return path


def get_memory_context():
    data = load()
    lines = []

    user = data.get("user", {})
    if user.get("name"):
        lines.append(f"User's name: {user['name']}")

    preferences = data.get("preferences", {})
    if isinstance(preferences, list):
        for p in preferences:
            lines.append(f"User preference: {p}")
    else:
        for key, value in preferences.items():
            lines.append(f"User preference ({key.replace('_', ' ')}): {value}")

    for item in data.get("learning", []):
        lines.append(f"User is learning: {item}")

    for fact in data.get("facts", []):
        lines.append(f"Known fact about user: {fact}")

    known_keys = {"user", "assistant", "preferences", "learning", "facts"}
    for key, value in data.items():
        if key in known_keys:
            continue
        _flatten(key, value, lines)

    return "\n".join(lines)