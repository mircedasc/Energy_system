from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
import pika
import json
import os
import threading
import asyncio
from typing import Dict, List

app = FastAPI()

# Variabilă globală pentru a stoca bucla principală de evenimente
main_loop = None


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        print(f" [WS] User {user_id} connected. Total connections for user: {len(self.active_connections[user_id])}",
              flush=True)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        print(f" [WS] User {user_id} disconnected.", flush=True)

    async def send_personal_message(self, message: str, user_id: int):
        # Aici verificăm dacă userul are conexiuni active
        if user_id in self.active_connections:
            print(f" [WS] Sending to User {user_id} (Connections: {len(self.active_connections[user_id])})", flush=True)
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(message)
                    print(" [WS] Message sent successfully via WebSocket.", flush=True)
                except Exception as e:
                    print(f" [ERROR] Could not send via WS: {e}", flush=True)
        else:
            print(f" [WS] User {user_id} is NOT connected. Message dropped.", flush=True)


manager = ConnectionManager()


# --- RABBITMQ CONSUMER ---
def start_rabbitmq_consumer():
    rabbitmq_host = os.getenv("RABBIT_HOST", "rabbitmq")
    queue_name = "notification_queue"

    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbitmq_host)
            )
            channel = connection.channel()
            channel.queue_declare(queue=queue_name, durable=True)

            print(" [*] RabbitMQ Consumer ready.", flush=True)

            def callback(ch, method, properties, body):
                try:
                    data = json.loads(body)
                    user_id = data.get("user_id")

                    #Nu extragem doar mesajul, ci trimitem tot obiectul JSON ca string
                    full_payload = json.dumps(data)

                    print(f" [RABBIT] Processing alert for User {user_id}", flush=True)

                    if user_id and main_loop:
                        asyncio.run_coroutine_threadsafe(
                            # Trimitem JSON-ul complet
                            manager.send_personal_message(full_payload, int(user_id)),
                            main_loop
                        )
                    else:
                        print(" [ERROR] Missing data or Main Loop not ready", flush=True)

                except Exception as e:
                    print(f" [ERROR] Callback error: {e}", flush=True)

            channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
            channel.start_consuming()

        except Exception as e:
            print(f" [CRITICAL] RabbitMQ lost. Retrying... {e}", flush=True)
            import time
            time.sleep(5)


@app.on_event("startup")
async def startup_event():
    global main_loop
    # Capturăm bucla principală unde rulează WebSocket-urile
    main_loop = asyncio.get_running_loop()

    # Pornim consumatorul în fundal
    consumer_thread = threading.Thread(target=start_rabbitmq_consumer, daemon=True)
    consumer_thread.start()


@app.websocket("/ws/connect/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Păstrăm conexiunea vie
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        manager.disconnect(websocket, user_id)