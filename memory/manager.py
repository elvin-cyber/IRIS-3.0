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
    FILE.write_text(
        json.dumps(data, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )


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