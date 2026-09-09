conversation=[]
def add_message(role,content):
    conversation.append({"role":role,"content":content})
    if len(conversation)>20: del conversation[:-20]
def get_recent_messages(limit=10): return conversation[-limit:]
