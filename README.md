# IRIS 3.0

## START
python main.py for text model in terminal 
python server.py for voice model ( http://127.0.0.1:5000 )

## EXIT
Type: exit

## INSTALL
pip install -r requirements.txt
ollama pull qwen2.5:7b-instruct

## ARCHITECTURE
User -> IRIS Core -> One Main AI Model -> Memory / Python Tools / Conversation -> Response

IRIS 3.0 uses one main AI model: qwen2.5:7b-instruct.
Python handles memory, tools and conversation storage.
