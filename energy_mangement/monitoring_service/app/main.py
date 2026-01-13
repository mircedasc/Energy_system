from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import pika
import json
import threading
from datetime import datetime
import os
import time
from typing import List
from . import schemas
from . import models, database

# Așteptăm puțin să pornească RabbitMQ
time.sleep(10)

app = FastAPI(root_path="/monitoring")

# --- CORS MIDDLEWARE (Critic pentru Frontend) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=database.engine)

# Config RabbitMQ
RABBIT_HOST = os.getenv("RABBIT_HOST", "rabbitmq")
QUEUE_NAME = "sensor_data"


def process_message(ch, method, properties, body):
    """
    Această funcție se execută pentru FIECARE mesaj primit.
    """
    try:
        data = json.loads(body)
        print(f" [x] Received data for device {data['device_id']}: {data['measurement_value']}", flush=True)

        # --- MODIFICARE CHEIE: ROTUNJIRE LA 10 MINUTE ---
        timestamp_ms = data['timestamp']
        dt_object = datetime.fromtimestamp(timestamp_ms / 1000.0)

        # Calculăm minutul rotunjit (0, 10, 20, 30, 40, 50)
        minute = dt_object.minute
        rounded_minute = (minute // 10) * 10

        # Creăm noul timestamp (ex: 10:14:55 devine 10:10:00)
        interval_start = dt_object.replace(minute=rounded_minute, second=0, microsecond=0)
        interval_timestamp = int(interval_start.timestamp() * 1000)
        # -----------------------------------------------

        # 2. Scriem în Baza de Date
        db = database.SessionLocal()
        try:
            # Căutăm în DB folosind noul timestamp de 10 minute
            record = db.query(models.HourlyConsumption).filter(
                models.HourlyConsumption.device_id == data['device_id'],
                models.HourlyConsumption.timestamp == interval_timestamp
            ).first()

            if record:
                # Dacă există deja intrarea pentru aceste 10 minute, adunăm la total
                record.total_consumption += data['measurement_value']
            else:
                # Dacă nu există, creăm rând nou
                new_record = models.HourlyConsumption(
                    device_id=data['device_id'],
                    timestamp=interval_timestamp,
                    total_consumption=data['measurement_value']
                )
                db.add(new_record)

            db.commit()
            print(" [v] Saved to DB", flush=True)

        except Exception as e:
            print(f"Error DB: {e}", flush=True)
        finally:
            db.close()

    except Exception as e:
        print(f"Error processing message: {e}", flush=True)


def start_consumer():
    """Funcția care rulează în background cu mecanism de RE-TRY"""
    while True:
        try:
            print(f" [*] Connecting to RabbitMQ at {RABBIT_HOST}...", flush=True)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBIT_HOST, heartbeat=600, blocked_connection_timeout=300)
            )
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.basic_consume(queue=QUEUE_NAME, on_message_callback=process_message, auto_ack=True)
            print(' [*] Successfully connected! Waiting for messages.', flush=True)
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError:
            print(" [!] RabbitMQ not ready yet. Retrying in 5 seconds...", flush=True)
            time.sleep(5)
        except Exception as e:
            print(f" [!] Connection lost: {e}. Retrying in 5 seconds...", flush=True)
            time.sleep(5)


@app.on_event("startup")
def startup_event():
    t = threading.Thread(target=start_consumer)
    t.daemon = True
    t.start()


@app.get("/consumption/{device_id}", response_model=List[schemas.ConsumptionRecord])
def get_device_consumption(device_id: int, db: Session = Depends(database.get_db)):
    """ Endpoint pentru Frontend (Grafice) """
    records = db.query(models.HourlyConsumption).filter(
        models.HourlyConsumption.device_id == device_id
    ).order_by(models.HourlyConsumption.timestamp).all()

    return records