import json
from pathlib import Path
FILE=Path(__file__).parent/"memory.json"
DEFAULT={"user":{"name":"Elvin"},"assistant":{"name":"IRIS","full_form":"Information Reasoning Interaction System","purpose":"A personal AI assistant designed to understand the user, remember what matters, help solve problems, manage tasks, and make everyday life easier."},"preferences":{"general":"short answers"},"learning":["Linux","Networking","Cybersecurity"],"facts":["Studying Linux for technical support role"]}

def load():
    if not FILE.exists(): save(DEFAULT)
    try:return json.loads(FILE.read_text(encoding="utf-8"))
    except:return DEFAULT.copy()
def save(data):FILE.write_text(json.dumps(data,indent=4),encoding="utf-8")
def get_user_name():return load().get("user",{}).get("name")
def get_assistant_info():return load().get("assistant",DEFAULT["assistant"])
def add_memory(category,fact):
    d=load();fact=str(fact).strip()
    if category=="name":d.setdefault("user",{})["name"]=fact
    elif category=="preference":d.setdefault("preferences",{})["general"]=fact
    elif category=="learning":
        d.setdefault("learning",[])
        if fact not in d["learning"]:d["learning"].append(fact)
    else:
        d.setdefault("facts",[])
        if fact not in d["facts"]:d["facts"].append(fact)
    save(d)
def get_memory_context():
    d=load();lines=[]
    if d.get("user",{}).get("name"):lines.append("User's name: "+d["user"]["name"])
    for k,v in d.get("preferences",{}).items():lines.append(f"Preference: {k} = {v}")
    lines += ["Learning: "+x for x in d.get("learning",[])]
    lines += ["Fact: "+x for x in d.get("facts",[])]
    return "\n".join(lines)
