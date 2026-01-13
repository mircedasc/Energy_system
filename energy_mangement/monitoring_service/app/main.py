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

# Așteptăm puțin să pornească RabbitMQ (retry mechanism e mai jos, dar asta ajută la startul inițial)
time.sleep(10)

app = FastAPI(root_path="/monitoring")

# --- CORS MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Creăm tabelele (include acum și MonitoredDevice dacă ai actualizat models.py)
models.Base.metadata.create_all(bind=database.engine)

# Config RabbitMQ
RABBIT_HOST = os.getenv("RABBIT_HOST", "rabbitmq")
QUEUE_SENSOR_DATA = "sensor_data"
QUEUE_DEVICE_SYNC = "device_sync_queue"
QUEUE_NOTIFICATIONS = "notification_queue"

# ==================================================================================
# 1. CONSUMER PENTRU SENZORI (Calcul consum orar)
# ==================================================================================
def send_notification(user_id: int, message: str, device_id: int):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NOTIFICATIONS, durable=True)

        payload = {
            "user_id": user_id,
            "message": message,
            "device_id": device_id
        }

        channel.basic_publish(
            exchange='',
            routing_key=QUEUE_NOTIFICATIONS,
            body=json.dumps(payload)
        )
        connection.close()
        print(f" [ALERT] Sent notification for User {user_id}", flush=True)
    except Exception as e:
        print(f"Error sending notification: {e}", flush=True)


def process_sensor_message(ch, method, properties, body):
    """ Procesează datele de consum cu DEBUG LOGGING """
    db = database.SessionLocal()
    try:
        data = json.loads(body)
        device_id = data.get('device_id')
        measurement = data.get('measurement_value')

        print(f" [SENSOR] Received: Device {device_id}, Value {measurement}", flush=True)

        # 1. Calculăm timestamp-ul rotunjit (logica ta existentă)
        timestamp_ms = data['timestamp']
        dt_object = datetime.fromtimestamp(timestamp_ms / 1000.0)
        minute = dt_object.minute
        rounded_minute = (minute // 10) * 10
        interval_start = dt_object.replace(minute=rounded_minute, second=0, microsecond=0)
        interval_timestamp = int(interval_start.timestamp() * 1000)

        # 2. Salvăm/Actualizăm consumul
        record = db.query(models.HourlyConsumption).filter(
            models.HourlyConsumption.device_id == device_id,
            models.HourlyConsumption.timestamp == interval_timestamp
        ).first()

        if record:
            record.total_consumption += measurement
        else:
            record = models.HourlyConsumption(
                device_id=device_id,
                timestamp=interval_timestamp,
                total_consumption=measurement
            )
            db.add(record)

        db.commit()
        # Facem refresh ca să fim siguri că avem valoarea actualizată din DB
        db.refresh(record)
        print(f" [DB] Total Consumption for Device {device_id} is now: {record.total_consumption}", flush=True)

        # =================================================================
        # 3. VERIFICAREA PENTRU ALERTĂ (DEBUGGING)
        # =================================================================

        # Căutăm setările device-ului
        device_settings = db.query(models.MonitoredDevice).filter(
            models.MonitoredDevice.device_id == device_id
        ).first()

        if not device_settings:
            print(f" [DEBUG] ❌ Device {device_id} NOT FOUND in 'monitored_devices' table!", flush=True)
            print(" [DEBUG] Hint: Did you sync the device or insert it manually?", flush=True)

        else:
            current_total = record.total_consumption
            max_limit = device_settings.max_hourly_consumption

            print(f" [DEBUG] 🔍 Checking Limit: Current ({current_total}) > Max ({max_limit})?", flush=True)

            if max_limit > 0 and current_total > max_limit:
                print(" [DEBUG] 🚨 LIMIT EXCEEDED! Sending alert...", flush=True)

                msg = f"Alert! Device {device_id} exceeded limit! Current: {current_total:.2f}, Max: {max_limit}"
                send_notification(device_settings.user_id, msg, device_id)
            else:
                print(" [DEBUG] ✅ Limit OK (or limit is 0). No alert sent.", flush=True)

    except Exception as e:
        print(f"Error processing sensor message: {e}", flush=True)
    finally:
        db.close()


def start_sensor_consumer():
    """ Thread care ascultă coada 'sensor_data' """
    while True:
        try:
            print(f" [*] [SENSOR] Connecting to RabbitMQ...", flush=True)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBIT_HOST, heartbeat=600, blocked_connection_timeout=300)
            )
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_SENSOR_DATA, durable=True)
            channel.basic_consume(queue=QUEUE_SENSOR_DATA, on_message_callback=process_sensor_message, auto_ack=True)
            print(' [*] [SENSOR] Connected! Waiting for measurements.', flush=True)
            channel.start_consuming()
        except Exception as e:
            print(f" [!] [SENSOR] Connection lost: {e}. Retrying in 5s...", flush=True)
            time.sleep(5)


# ==================================================================================
# 2. CONSUMER PENTRU SINCRONIZARE (Update Device List) - CERINȚA A2/A3
# ==================================================================================

def process_sync_message(ch, method, properties, body):
    """ Procesează evenimente de sincronizare (CREATE/UPDATE/DELETE Device) """
    try:
        data = json.loads(body)
        operation = data.get("operation")
        device_id = data.get("device_id")

        print(f" [SYNC] Received {operation} for device {device_id}", flush=True)

        db = database.SessionLocal()
        try:
            # Folosim modelul MonitoredDevice adăugat în models.py
            if operation in ["CREATE", "UPDATE"]:
                existing = db.query(models.MonitoredDevice).filter(
                    models.MonitoredDevice.device_id == device_id).first()

                if existing:
                    existing.user_id = data.get("user_id")
                    existing.max_hourly_consumption = data.get("max_hourly_consumption")
                    print(f" [SYNC] Updated Device {device_id}")
                else:
                    new_dev = models.MonitoredDevice(
                        device_id=device_id,
                        user_id=data.get("user_id"),
                        max_hourly_consumption=data.get("max_hourly_consumption")
                    )
                    db.add(new_dev)
                    print(f" [SYNC] Created Device {device_id}")

                db.commit()

            elif operation == "DELETE":
                db.query(models.MonitoredDevice).filter(models.MonitoredDevice.device_id == device_id).delete()
                db.commit()
                print(f" [SYNC] Deleted Device {device_id}")

        except Exception as e:
            print(f"Error Sync DB: {e}", flush=True)
        finally:
            db.close()

    except Exception as e:
        print(f"Error processing sync message: {e}", flush=True)


def start_sync_consumer():
    """ Thread care ascultă coada 'device_sync_queue' """
    while True:
        try:
            print(f" [*] [SYNC] Connecting to RabbitMQ...", flush=True)
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBIT_HOST, heartbeat=600, blocked_connection_timeout=300)
            )
            channel = connection.channel()
            # Declarăm coada ca durable=True ca să nu pierdem mesaje dacă monitoring e jos
            channel.queue_declare(queue=QUEUE_DEVICE_SYNC, durable=True)
            channel.basic_consume(queue=QUEUE_DEVICE_SYNC, on_message_callback=process_sync_message, auto_ack=True)
            print(' [*] [SYNC] Connected! Waiting for sync events.', flush=True)
            channel.start_consuming()
        except Exception as e:
            print(f" [!] [SYNC] Connection lost: {e}. Retrying in 5s...", flush=True)
            time.sleep(5)


# ==================================================================================
# 3. STARTUP & ENDPOINTS
# ==================================================================================

@app.on_event("startup")
def startup_event():
    # Pornim Thread-ul 1: Senzori (Date Simulator)
    t1 = threading.Thread(target=start_sensor_consumer, daemon=True)
    t1.start()

    # Pornim Thread-ul 2: Sincronizare (Date Device Service)
    t2 = threading.Thread(target=start_sync_consumer, daemon=True)
    t2.start()


@app.get("/consumption/{device_id}", response_model=List[schemas.ConsumptionRecord])
def get_device_consumption(device_id: int, db: Session = Depends(database.get_db)):
    records = db.query(models.HourlyConsumption).filter(
        models.HourlyConsumption.device_id == device_id
    ).order_by(models.HourlyConsumption.timestamp).all()
    return records