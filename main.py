from core.iris import respond
from memory.manager import get_user_name

print(f"IRIS: Hello {get_user_name() or 'there'}! How can I help you?")
print("Type 'exit' to close IRIS.\n")

while True:
    user_input=input("You: ").strip()
    if not user_input: continue
    if user_input.lower() in {"exit","quit","bye"}:
        print(f"IRIS: Goodbye, {get_user_name() or 'there'}! 👋")
        break
    print(f"IRIS: {respond(user_input)}\n")
