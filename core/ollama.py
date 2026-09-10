import requests, threading, time, sys
OLLAMA_URL="http://localhost:11434/api/chat"
MODEL="qwen2.5:14b-instruct"

def think(stop):
    dots=0
    while not stop.is_set():
        sys.stdout.write("\rIRIS is thinking"+"."*dots+"   ");sys.stdout.flush()
        dots=(dots+1)%4;time.sleep(.4)
    sys.stdout.write("\r"+" "*40+"\r");sys.stdout.flush()

def ask_iris(messages):
    stop=threading.Event()
    t=threading.Thread(target=think,args=(stop,),daemon=True);t.start()
    try:
        r=requests.post(OLLAMA_URL,json={"model":MODEL,"messages":messages,"stream":False,"options":{"temperature":0.3,"num_predict":400}},timeout=180)
        r.raise_for_status()
        return r.json()["message"]["content"].strip() or "I couldn't come up with an answer."
    except requests.exceptions.ConnectionError:
        return "I can't connect to Ollama. Please make sure Ollama is running."
    except requests.exceptions.Timeout:
        return "I took too long to respond."
    except Exception as e:
        return f"AI error: {e}"
    finally:
        stop.set();t.join()
