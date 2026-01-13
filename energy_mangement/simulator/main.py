import pika
import json
import time
import random
import sys
import threading  # <--- Import necesar pentru paralelism
from datetime import datetime, timedelta

# 1. Citim Configurația (Listă de ID-uri)
DEVICE_IDS = [1]  # Default
try:
    with open('config.json', 'r') as f:
        config = json.load(f)
        # Citim lista, sau un singur ID dacă e formatul vechi
        if "device_ids" in config:
            DEVICE_IDS = config["device_ids"]
        elif "device_id" in config:
            DEVICE_IDS = [config["device_id"]]
except:
    print(" [!] Config file not found or invalid. Using default ID: 1")

# Configurare RabbitMQ
RABBIT_HOST = 'localhost'
QUEUE_NAME = 'sensor_data'


def generate_sensor_value():
    current_hour = datetime.now().hour
    base_load = 0.5
    if 18 <= current_hour <= 22:
        base_load += 2.0
    elif 8 <= current_hour <= 17:
        base_load += 1.0
    return max(0, round(base_load + random.uniform(-0.2, 0.5), 2))


def simulate_single_device(device_id):
    """
    Această funcție rulează independent pentru FIECARE device.
    Are propria conexiune la RabbitMQ și propriul timp simulat.
    """
    try:
        # Fiecare thread își face propria conexiune (Thread-Safe)
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)

        # Adăugăm un mic delay random la start ca să nu trimită toți fix în aceeași milisecundă
        time.sleep(random.uniform(0, 2))

        print(f" [*] Thread pornit pentru Device ID: {device_id}")

        simulated_time = datetime.now()

        while True:
            timestamp = simulated_time.timestamp() * 1000
            value = generate_sensor_value()

            payload = {
                "timestamp": int(timestamp),
                "device_id": device_id,
                "measurement_value": value
            }

            message = json.dumps(payload)

            channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=message)

            print(f" -> [Dev {device_id}] sent val: {value}")

            simulated_time += timedelta(minutes=10)

            time.sleep(random.uniform(0.5, 1.5))

    except Exception as e:
        print(f" [!] Eroare thread device {device_id}: {e}")
    finally:
        if 'connection' in locals() and connection.is_open:
            connection.close()


def main():
    print(f" [!!!] Pornire simulator MULTI-DEVICE pentru ID-urile: {DEVICE_IDS}")
    print(" [!!!] Apasa CTRL+C (in repetate randuri) pentru a opri tot.")

    threads = []

    # Creăm câte un thread pentru fiecare ID din listă
    for d_id in DEVICE_IDS:
        t = threading.Thread(target=simulate_single_device, args=(d_id,))
        t.daemon = True  # Se opresc când se oprește programul principal
        t.start()
        threads.append(t)

    # Ținem programul principal viu
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n [!!!] Oprire simulatoare...")
        sys.exit(0)


if __name__ == '__main__':
    main()