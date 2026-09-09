import json,re
TOOLS={"system","ram","disk","cpu","hostname","current_user","ipconfig","windows_version"}

def decide_action(ask_iris,message,memory,conversation):
    prompt=f"""You are the action brain of IRIS. Choose what to do with the user's message.

Actions:
answer = normal conversation or knowledge question
memory = user provides or changes personal information
tool = live computer information is required

Tools: system, ram, disk, cpu, hostname, current_user, ipconfig, windows_version

Stored memory:
{memory}

Recent conversation:
{conversation}

User message: {message}

Return ONLY JSON.
Examples:
{{"action":"answer"}}
{{"action":"memory","category":"name","fact":"Elvin"}}
{{"action":"tool","tool":"ram"}}

Memory categories: name, preference, learning, fact.
"What is my name?" is answer, because memory can answer it.
"How much RAM am I using?" is tool.
"My name is Elvin" and "Change my name to Elvin" are memory."""
    raw=ask_iris([{"role":"system","content":"Return only valid JSON. No explanation."},{"role":"user","content":prompt}])
    match=re.search(r"\{.*?\}",raw,re.S)
    if not match:return {"action":"answer"}
    try:d=json.loads(match.group())
    except:return {"action":"answer"}
    if d.get("action")=="tool" and d.get("tool") not in TOOLS:return {"action":"answer"}
    if d.get("action") not in {"answer","memory","tool"}:return {"action":"answer"}
    return d
