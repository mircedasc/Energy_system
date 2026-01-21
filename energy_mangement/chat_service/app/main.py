from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pika
import json
import os
import google.generativeai as genai

app = FastAPI()

# --- CONSTANTE ---
ADMIN_ID = 1

# --- CONFIGURARE CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURARE AI (CU DETECTARE AUTOMATĂ) ---
api_key = os.getenv("GEMINI_API_KEY")
model = None

if api_key:
    try:
        genai.configure(api_key=api_key)

        print(" [AI DEBUG] Caut un model valid...", flush=True)
        available_models = []
        # Listăm modelele disponibile pentru contul tău
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)

        # Algoritm de selecție: Preferăm Flash -> Pro -> Primul găsit
        selected_model = None
        preferences = ["models/gemini-1.5-flash", "models/gemini-pro", "models/gemini-1.0-pro"]

        for pref in preferences:
            if pref in available_models:
                selected_model = pref
                break

        if not selected_model and available_models:
            selected_model = available_models[0]  # Fallback la orice avem

        if selected_model:
            # Important: API-ul uneori vrea "models/gemini-pro", alteori doar "gemini-pro"
            # Curățăm prefixul pentru instanțiere dacă e nevoie, dar de obicei merge cu numele full din listă
            print(f" [AI DEBUG] Am selectat modelul: {selected_model}", flush=True)
            model = genai.GenerativeModel(selected_model)
        else:
            print(" [AI ERROR] Nu am găsit niciun model compatibil!", flush=True)

    except Exception as e:
        print(f" [AI ERROR] Configurare eșuată: {e}", flush=True)
else:
    print(" [WARNING] GEMINI_API_KEY not found!", flush=True)


class Message(BaseModel):
    sender_id: int
    message: str
    is_admin: bool = False


# --- RABBITMQ HELPER ---
def send_to_websocket(target_user_id, message_text, sender_role="System"):
    try:
        rabbitmq_host = os.getenv("RABBIT_HOST", "rabbitmq")
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
        channel = connection.channel()
        channel.queue_declare(queue='notification_queue', durable=True)

        payload = {
            "user_id": target_user_id,
            "message": f"[{sender_role}]: {message_text}",
            "type": "chat"
        }

        channel.basic_publish(
            exchange='',
            routing_key='notification_queue',
            body=json.dumps(payload)
        )
        connection.close()
    except Exception as e:
        print(f" [ERROR] RabbitMQ: {e}", flush=True)


# --- RUTA PRINCIPALĂ ---
@app.post("/chat/send")
async def send_message(msg: Message):
    print(f" [CHAT] {msg.sender_id}: {msg.message}", flush=True)

    # 1. ADMIN -> CLIENT
    if msg.is_admin:
        send_to_websocket(msg.sender_id, msg.message, sender_role="Admin")
        return {"status": "Sent by Admin"}

    # 2. CLIENT -> SISTEM
    text = msg.message.lower()
    keywords_admin = ["/admin"]

    # A. Cere Operator
    if any(k in text for k in keywords_admin):
        send_to_websocket(ADMIN_ID, f"CLIENT {msg.sender_id} cere ajutor: {msg.message}",
                          sender_role=f"Client {msg.sender_id}")
        send_to_websocket(msg.sender_id, "Un operator a fost notificat.", sender_role="System")
        return {"status": "Notified Admin"}

    # B. Reguli + AI
    response = ""
    role = "Support Bot"

    if "program" in text:
        response = "Luni-Vineri: 09:00 - 17:00."
    elif "contact" in text:
        response = "Email: contact@energy.com"
    elif "pret" in text:
        response = "Pretul este de 0.80 RON pe kW."
    elif "ajutor" in text:
        response = "Daca ai nevoie sa contactezi un operator foloseste "+ "/admin" + " in fata mesajului tau."
    else:
        # AI Logic
        if model:
            try:

                prompt = f"Ești un asistent expert în energie; răspunde scurt și politicos în română, nu inventa date personale și direcționează problemele tehnice către un operator. Întrebarea este: {msg.message}"
                ai_response = model.generate_content(prompt)
                response = ai_response.text
                role = "AI Assistant"
            except Exception as e:
                # Aici prindem eroarea exactă dacă tot nu merge
                print(f" [AI GENERATE ERROR] {e}", flush=True)
                response = "AI indisponibil momentan."
        else:
            response = "AI neconfigurat."

    send_to_websocket(msg.sender_id, response, sender_role=role)
    return {"status": "Processed"}