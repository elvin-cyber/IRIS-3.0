import json
import re


TOOLS = {
    "system", "ram", "disk", "cpu", "hostname",
    "current_user", "ipconfig", "windows_version",
}


_NAME_PATTERNS = [
    r"^(?:please\s+)?call me\s+(.+)$",
    r"^(?:please\s+)?you can call me\s+(.+)$",
    r"^my name is\s+(.+)$",
    r"^my new name is\s+(.+)$",
    r"^change my name to\s+(.+)$",
    r"^change my name as\s+(.+)$",
    r"^set my name to\s+(.+)$",
    r"^set my name as\s+(.+)$",
    r"^update my name to\s+(.+)$",
    r"^rename me to\s+(.+)$",
    r"^rename me as\s+(.+)$",
    r"^switch my name to\s+(.+)$",
    r"^make my name\s+(.+)$",
    r"^name me\s+(.+)$",
    r"^i(?:'d| would) like to be called\s+(.+)$",
    r"^i want to be called\s+(.+)$",
    r"^i go by\s+(.+)$",
    r"^i(?:'m| am) known as\s+(.+)$",
    r"^refer to me as\s+(.+)$",
    r"^address me as\s+(.+)$",
    r"^from now on,? call me\s+(.+)$",
    r"^from now on,? my name is\s+(.+)$",
]

_PREFERENCE_PATTERNS = [
    r"^my favorite (.+?) is (.+)$",
    r"^i (?:like|love|prefer|enjoy)\s+(.+)$",
]

_LEARNING_PATTERNS = [
    r"^i(?:'m| am) (?:learning|studying)\s+(.+)$",
]

_FACT_PATTERNS = [
    r"^my (.+?) is (.+)$",
    r"^i have (?:a|an)\s+(.+)$",
]

_DELETE_PATTERNS = [
    r"^forget (?:that )?my (.+)$",
    r"^forget about my (.+)$",
    r"^delete my (.+)$",
    r"^remove my (.+)$",
    r"^clear my (.+)$",
    r"^i don'?t want you to remember my (.+)$",
    r"^stop remembering my (.+)$",
]

_UPDATE_PATTERNS = [
    r"^change my (.+?) to (.+)$",
    r"^update my (.+?) to (.+)$",
    r"^set my (.+?) to (.+)$",
]

# =========================================================
# DYNAMIC-SECTION PATTERNS
#
# These catch common, high-confidence phrasings and route
# them straight into a structured section (family, pets, etc.)
# with a proper subject, BEFORE the generic _FACT_PATTERNS
# above would otherwise swallow them as a flat "fact" string.
# =========================================================

_FAMILY_RELATIONS = (
    "father", "dad", "mother", "mum", "mom", "sister", "brother",
    "wife", "husband", "son", "daughter", "grandfather", "grandmother",
    "uncle", "aunt", "cousin",
)

_FAMILY_NAME_PATTERN = re.compile(
    r"^my (" + "|".join(_FAMILY_RELATIONS) + r")'?s?\s+name is\s+(.+)$"
)

_NEW_PET_PATTERN = re.compile(
    r"^i (?:got|have|adopted|bought) a new (?:dog|cat|pet|puppy|kitten)"
    r"(?:\s+named|\s+called)?\s+([A-Za-z]+)"
)

_PET_BREED_TAIL_PATTERN = re.compile(
    r"(?:he'?s|she'?s|it'?s|who is)\s+a\s+(.+)$"
)


def _try_dynamic_patterns(text, lower):
    m = _FAMILY_NAME_PATTERN.match(lower)
    if m:
        relation = m.group(1)
        name = text[m.start(2):m.end(2)].strip()
        return {
            "action": "memory",
            "category": "family",
            "subject": relation,
            "fact": f"name: {name}",
        }

    m = _NEW_PET_PATTERN.match(lower)
    if m:
        name = text[m.start(1):m.end(1)].strip()
        breed_match = _PET_BREED_TAIL_PATTERN.search(lower)
        if breed_match:
            breed = text[breed_match.start(1):breed_match.end(1)].strip().rstrip(".")
            fact = f"breed: {breed}"
        else:
            fact = "new pet"
        return {
            "action": "memory",
            "category": "pets",
            "subject": name,
            "fact": fact,
        }

    return None

# =========================================================
# QUESTION DETECTION
#
# If the message is clearly a question, force "answer"
# immediately, regardless of what the LLM would decide.
# This closes the loophole where compound questions like
# "what's my X and my Y" get misclassified as memory writes.
# =========================================================

_QUESTION_STARTERS = (
    "what", "whats", "what's",
    "who", "whos", "who's",
    "where", "wheres", "where's",
    "when", "whens", "when's",
    "why",
    "how", "hows", "how's",
    "is", "are", "am",
    "do", "does", "did",
    "can", "could", "should", "would", "will",
)

# =========================================================
# TOOL KEYWORD DETECTION
#
# If a question mentions one of these, route straight to the
# matching tool instead of letting the generic question
# pre-filter force it to "answer".
# =========================================================

_TOOL_KEYWORDS = [
    ("ram", "ram"),
    ("memory usage", "ram"),
    ("disk space", "disk"),
    ("storage", "disk"),
    ("disk", "disk"),
    ("cpu", "cpu"),
    ("processor", "cpu"),
    ("computer name", "hostname"),
    ("hostname", "hostname"),
    ("pc name", "hostname"),
    ("logged in as", "current_user"),
    ("current user", "current_user"),
    ("ip address", "ipconfig"),
    ("ip config", "ipconfig"),
    ("ipconfig", "ipconfig"),
    ("windows version", "windows_version"),
    ("os version", "windows_version"),
    ("system info", "system"),
    ("system information", "system"),
]


def _detect_tool(lower):
    for keyword, tool in _TOOL_KEYWORDS:
        if keyword in lower:
            return tool
    return None


def _is_question(text_lower):
    if text_lower.endswith("?"):
        return True
    first_word = text_lower.split(" ", 1)[0].strip(",.!") if text_lower else ""
    return first_word in _QUESTION_STARTERS


def _prefilter(message):
    text = message.strip()
    lower = text.lower()

    # Statement patterns take priority — e.g. "my name is X"
    # should still save even though it doesn't end in "?".
    for pat in _NAME_PATTERNS:
        m = re.match(pat, lower)
        if m:
            fact = text[m.start(1):m.end(1)].strip()
            # Strip trailing filler like "from now on" / "please"
            # so it doesn't get duplicated in the reply template.
            fact = re.sub(r"\s*,?\s*from now on\.?$", "", fact, flags=re.I).strip()
            fact = re.sub(r"\s*,?\s*please\.?$", "", fact, flags=re.I).strip()
            fact = fact.rstrip(".").strip()
            if fact:
                return {"action": "memory", "category": "name", "fact": fact}

    for pat in _DELETE_PATTERNS:
        m = re.match(pat, lower)
        if m:
            query = text[m.start(1):m.end(1)].strip().rstrip(".").strip()
            if query:
                return {"action": "delete", "query": query}

    for pat in _UPDATE_PATTERNS:
        m = re.match(pat, lower)
        if m:
            field_query = text[m.start(1):m.end(1)].strip()
            new_value = text[m.start(2):m.end(2)].strip().rstrip(".").strip()
            if field_query and new_value:
                return {"action": "update", "query": field_query, "value": new_value}

    for pat in _PREFERENCE_PATTERNS:
        m = re.match(pat, lower)
        if m:
            return {"action": "memory", "category": "preference", "fact": text}

    for pat in _LEARNING_PATTERNS:
        m = re.match(pat, lower)
        if m:
            return {"action": "memory", "category": "learning", "fact": text}

    # High-confidence structured patterns take priority over the
    # generic catch-all fact pattern below.
    dynamic = _try_dynamic_patterns(text, lower)
    if dynamic:
        return dynamic

    for pat in _FACT_PATTERNS:
        m = re.match(pat, lower)
        if m:
            return {"action": "memory", "category": "fact", "fact": text}

    # Check tool keywords BEFORE forcing "answer" on questions —
    # "what is my ram" is a question, but it needs live data.
    tool = _detect_tool(lower)
    if tool:
        return {"action": "tool", "tool": tool}

    # No statement pattern or tool keyword matched — if it looks
    # like a question, force "answer" and skip the LLM entirely.
    if _is_question(lower):
        return {"action": "answer"}

    return None


def decide_action(ask_iris, message, memory, conversation):

    # Deterministic fast path — skip the LLM entirely if the
    # message obviously matches a statement/question/tool pattern.
    pre = _prefilter(message)
    if pre:
        return pre

    prompt = f"""
You are the action brain of IRIS, a personal AI assistant.

Choose exactly ONE action: answer, memory, delete, update, or tool.

Use "answer" for questions, general knowledge, or normal
conversation — including questions about stored information.
Questions must NEVER create or modify memory.

Use "memory" when the user states or changes personal
information (names, relationships, contact details,
preferences, favorites, what they're learning, possessions).

Memory categories: name, preference, learning, fact.

You may ALSO use a custom category for domain-specific info
that deserves its own section, such as "pets", "family",
"work", "vehicle", "hobbies", etc. When you do, also include
a "subject" naming the specific thing this is about (e.g. a
pet's name, a family member's relation, "car"). Example:

User: "I got a new cat named Milo, he's a Persian"
{{"action": "memory", "category": "pets", "subject": "Milo", "fact": "breed: Persian"}}

User: "my mother's birthday is 12 March"
{{"action": "memory", "category": "family", "subject": "mother", "fact": "birthday: 12 March"}}

If in doubt, or the fact doesn't fit any specific domain,
just use category "fact" with no subject.

Use "delete" when the user wants to forget, delete, remove or
erase previously stored information. Give either a free-text
"query" describing what to forget, or a precise "category"
(plus optional "subject" and "field") naming exactly what to
remove. Examples:

User: "remove Puffy from my pets"
{{"action": "delete", "category": "pets", "subject": "Puffy"}}

User: "forget my favorite colour"
{{"action": "delete", "query": "favorite colour"}}

Use "update" when the user wants to change the value of a
piece of information that is already stored, rather than add
something brand new. Give a "query" naming the field and the
new "value". Example:

User: "change my favourite colour to green"
{{"action": "update", "query": "favourite colour", "value": "green"}}

Use "tool" only when live computer information is needed.
Tools: system, ram, disk, cpu, hostname, current_user, ipconfig, windows_version.

Stored memory:
{memory}

Recent conversation:
{conversation}

User message: {message}

Return ONLY valid JSON, no markdown, no explanation.
Examples:
{{"action": "answer"}}
{{"action": "memory", "category": "fact", "fact": "mom's name is Nicy Antony"}}
{{"action": "memory", "category": "pets", "subject": "Milo", "fact": "breed: Persian"}}
{{"action": "tool", "tool": "ram"}}
"""

    try:
        raw = ask_iris([
            {"role": "system", "content": "You are an action classifier. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ])

        match = re.search(r"\{.*?\}", raw, re.DOTALL)
        if not match:
            return {"action": "answer"}

        decision = json.loads(match.group())
        action = decision.get("action")

        if action not in {"answer", "memory", "delete", "update", "tool"}:
            return {"action": "answer"}

        if action == "tool" and decision.get("tool") not in TOOLS:
            return {"action": "answer"}

        if action == "delete" and not decision.get("query") and not decision.get("category"):
            return {"action": "answer"}

        if action == "update" and not (decision.get("query") and decision.get("value")):
            return {"action": "answer"}

        if action == "memory":
            category = decision.get("category")
            fact = decision.get("fact")

            if not category or not isinstance(category, str):
                return {"action": "answer"}
            if not fact:
                return {"action": "answer"}

            # Fixed categories are trusted as-is. Anything else is
            # treated as a custom section name -- allow short,
            # sane-looking identifiers only (reject anything that
            # looks like garbage or an attempted injection).
            fixed = {"name", "preference", "learning", "fact"}
            if category not in fixed:
                if not re.match(r"^[A-Za-z][A-Za-z0-9 _-]{1,30}$", category):
                    return {"action": "answer"}

            # Safeguard: never let the LLM silently overwrite the
            # user's name unless the message explicitly says so.
            # This prevents things like tool output (e.g. the OS
            # username from the "current_user" tool) from getting
            # hallucinated into a name change.
            if decision.get("category") == "name":
                explicit = any(
                    re.match(p, message.strip().lower())
                    for p in _NAME_PATTERNS
                )
                if not explicit:
                    decision["category"] = "fact"

        return decision

    except Exception as error:
        print(f"[Brain Error] {error}")
        return {"action": "answer"}