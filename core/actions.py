import json
import re


TOOLS = {
    "system", "ram", "disk", "cpu", "hostname",
    "current_user", "ipconfig", "windows_version",
}


_NAME_PATTERNS = [
    r"^(?:change my name to|call me|my name is)\s+(.+)$",
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
            return {"action": "memory", "category": "name", "fact": fact}

    for pat in _PREFERENCE_PATTERNS:
        m = re.match(pat, lower)
        if m:
            return {"action": "memory", "category": "preference", "fact": text}

    for pat in _LEARNING_PATTERNS:
        m = re.match(pat, lower)
        if m:
            return {"action": "memory", "category": "learning", "fact": text}

    for pat in _FACT_PATTERNS:
        m = re.match(pat, lower)
        if m:
            return {"action": "memory", "category": "fact", "fact": text}

    # No statement pattern matched — if it looks like a
    # question, force "answer" and skip the LLM entirely.
    if _is_question(lower):
        return {"action": "answer"}

    return None


def decide_action(ask_iris, message, memory, conversation):

    pre = _prefilter(message)
    if pre:
        return pre

    prompt = f"""
You are the action brain of IRIS, a personal AI assistant.

Choose exactly ONE action: answer, memory, or tool.

Use "answer" for questions, general knowledge, or normal
conversation — including questions about stored information.
Questions must NEVER create or modify memory.

Use "memory" when the user states or changes personal
information (names, relationships, contact details,
preferences, favorites, what they're learning, possessions).

Memory categories: name, preference, learning, fact.

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

        if action not in {"answer", "memory", "tool"}:
            return {"action": "answer"}

        if action == "tool" and decision.get("tool") not in TOOLS:
            return {"action": "answer"}

        if action == "memory":
            if decision.get("category") not in {"name", "preference", "learning", "fact"}:
                return {"action": "answer"}
            if not decision.get("fact"):
                return {"action": "answer"}

        return decision

    except Exception as error:
        print(f"[Brain Error] {error}")
        return {"action": "answer"}