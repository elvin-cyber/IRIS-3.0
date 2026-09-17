# 🌸 IRIS 3.0

![IRIS](iris.png)

> **Your local AI assistant — running on your own computer.**

---

## 🚀 Start Here

There are **2 ways to use IRIS**:

| You want to... | Run |
|---|---|
| 💻 Chat in the terminal | `python main.py` |
| 🌐 Use the website | `python server.py` |

Before starting, make sure **Ollama is installed and running**.

---

# 1️⃣ First-Time Setup

Open **PowerShell / Terminal** inside the IRIS folder.

### Install Python packages

```bash
pip install -r requirements.txt
```

### Download the AI model

```bash
ollama pull qwen2.5:14b-instruct
```

### Check that Ollama sees the model

```bash
ollama list
```

You should see:

```text
qwen2.5:14b-instruct
```

---

# 2️⃣ 💻 Use IRIS in the Terminal

Run:

```bash
python main.py
```

You should see something like:

```text
IRIS: Hello ...
You:
```

Now simply type:

```text
You: Hello IRIS
```

### 🛑 Stop IRIS

Press:

```text
Ctrl + C
```

or type:

```text
exit
```

---

# 3️⃣ 🌐 Use the IRIS Website

Start the server:

```bash
python server.py
```

Then open your browser:

👉 **http://127.0.0.1:5000**

### In the website

**💬 Text**
1. Type your message.
2. Click **SEND**.

**🎙️ Voice**
1. Click the microphone.
2. Speak.
3. IRIS processes your request.
4. IRIS can speak the response.

**🟢 MODEL ONLINE**

Means the website can communicate with the AI backend.

### 🛑 Stop the website

Go back to the terminal running `server.py` and press:

```text
Ctrl + C
```

---

# 4️⃣ 🧠 How IRIS Works

Think of IRIS like this:

```text
             YOU
              │
       ┌──────┴──────┐
       ▼             ▼
   💻 Terminal    🌐 Website
    main.py       server.py
       │             │
       └──────┬──────┘
              ▼
        🧠 IRIS CORE
       core/iris.py
              │
       ┌──────┼──────┐
       ▼      ▼      ▼
    🧠 Memory 🛠️ Tools 🤖 AI
       │      │      │
       └──────┼──────┘
              ▼
           Ollama
              │
              ▼
           Response
```

### Remember this:

```text
main.py   → Terminal
server.py → Website
core/     → IRIS logic
memory/   → Long-term memory
tools/    → Computer/system tools
Ollama    → AI model
static/   → Website files
```

---

# 5️⃣ 🧠 IRIS Memory

IRIS keeps long-term memory in:

```text
memory/memory.json
```

You can tell IRIS:

```text
Remember that my name is John.
```

Ask:

```text
What do you remember about me?
```

Change something:

```text
Change my name to Alex.
```

Forget something:

```text
Forget my name.
```

⚠️ **Do not delete `memory.json` unless you want to remove the stored memory.**

---

# 6️⃣ 🛠️ System Tools

IRIS can use Python tools to obtain information from your computer.

For example:

```text
What is my CPU?
What is my RAM usage?
How much disk space do I have?
What is my hostname?
What is my IP address?
```

The important idea:

```text
Question
   ↓
IRIS decides what is needed
   ↓
Python tool gets information
   ↓
IRIS gives you the answer
```

---

# 7️⃣ 📁 Important Files

| File / Folder | What it does |
|---|---|
| `main.py` | 💻 Terminal interface |
| `server.py` | 🌐 Web server |
| `core/iris.py` | 🧠 Main IRIS logic |
| `core/actions.py` | 🔎 Handles actions |
| `core/ollama.py` | 🤖 Talks to Ollama |
| `core/context.py` | 💬 Conversation context |
| `memory/manager.py` | 🧠 Manages memory |
| `memory/memory.json` | 💾 Saved memory |
| `tools/system_tools.py` | 🛠️ System information |
| `static/index.html` | 🌐 Website structure |
| `static/style.css` | 🎨 Website design |
| `static/app.js` | ⚙️ Website behavior |

---

# 8️⃣ 🔧 Ollama Commands

### See installed models

```bash
ollama list
```

### Download IRIS's model

```bash
ollama pull qwen2.5:14b-instruct
```

### Test the model directly

```bash
ollama run qwen2.5:14b-instruct
```

### Start Ollama manually

```bash
ollama serve
```

⚠️ If Ollama is already running, you **do not need** another `ollama serve`.

---

# 9️⃣ ❌ Troubleshooting

### IRIS cannot connect to Ollama

Try:

```bash
ollama list
```

If Ollama isn't running:

```bash
ollama serve
```

Then test:

```bash
ollama run qwen2.5:14b-instruct
```

---

### 🌐 Website doesn't open

Make sure this is running:

```bash
python server.py
```

Then visit:

```text
http://127.0.0.1:5000
```

---

### 📦 Python package error

Run:

```bash
pip install -r requirements.txt
```

---

# 🔟 ⚡ Quick Cheat Sheet

## Start terminal IRIS

```bash
python main.py
```

## Start website

```bash
python server.py
```

## Open website

```text
http://127.0.0.1:5000
```

## Check Ollama

```bash
ollama list
```

## Start Ollama

```bash
ollama serve
```

## Stop anything running in terminal

```text
Ctrl + C
```

---

# 🧩 The One-Minute Explanation

If you forget everything else, remember:

```text
👤 YOU
 │
 ▼
💻 main.py       → Terminal
🌐 server.py     → Website
 │
 ▼
🧠 core/iris.py  → IRIS's main logic
 │
 ├── 🧠 memory/  → Remembers things
 ├── 🛠️ tools/   → Checks your computer
 │
 ▼
🤖 Ollama        → Runs the AI model
 │
 ▼
💬 IRIS RESPONSE
```

**That's IRIS. 🌸**
