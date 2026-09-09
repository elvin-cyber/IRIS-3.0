import json
from pathlib import Path


FILE = Path(__file__).parent / "memory.json"


DEFAULT = {
    "user": {
        "name": "Elvin"
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
    "preferences": ["short answers"],
    "learning": ["Linux", "Networking", "Cybersecurity"],
    "facts": []
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


def add_memory(category, fact):
    data = load()
    fact = str(fact).strip()
    if not fact:
        return

    if category == "name":
        data.setdefault("user", {})["name"] = fact

    elif category == "preference":
        preferences = data.setdefault("preferences", [])
        if isinstance(preferences, dict):
            preferences = list(preferences.values())
            data["preferences"] = preferences
        if fact not in preferences:
            preferences.append(fact)

    elif category == "learning":
        learning = data.setdefault("learning", [])
        if fact not in learning:
            learning.append(fact)

    else:
        facts = data.setdefault("facts", [])
        if fact not in facts:
            facts.append(fact)

    save(data)


# =========================================================
# GENERIC FLATTENER
#
# Walks ANY nested dict/list under memory.json (family,
# personal, pets, work, or anything you add later) and turns
# it into readable lines, so manually-added or future custom
# categories are automatically visible to IRIS without
# needing code changes every time.
# =========================================================

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

    preferences = data.get("preferences", [])
    if isinstance(preferences, dict):
        preferences = list(preferences.values())
    for p in preferences:
        lines.append(f"User preference: {p}")

    for item in data.get("learning", []):
        lines.append(f"User is learning: {item}")

    for fact in data.get("facts", []):
        lines.append(f"Known fact about user: {fact}")

    # Everything else (family, personal, pets, work, or any
    # future custom top-level key) gets picked up here.
    known_keys = {"user", "assistant", "preferences", "learning", "facts"}
    for key, value in data.items():
        if key in known_keys:
            continue
        _flatten(key, value, lines)

    return "\n".join(lines)