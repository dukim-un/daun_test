# app/consumer.py
from kafka import KafkaConsumer
import mysql.connector
import json
import os

DB_HOST = os.getenv("MYSQL_HOST", "mysql")
DB_USER = os.getenv("MYSQL_USER", "zcon")
DB_PASS = os.getenv("MYSQL_PASSWORD", "toor")
DB_NAME = os.getenv("MYSQL_DATABASE", "test")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka.kafka.svc.cluster.local:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "test-topic")

# MySQL 연결
conn = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASS,
    database=DB_NAME
)
cursor = conn.cursor()


def safe_json_loads(m):
    if not m:
        return None
    try:
        return json.loads(m.decode('utf-8'))
    except Exception as e:
        print(f"[WARN] JSON decode failed: {e}, raw message: {m}")
        return None

#kafka connect
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=[KAFKA_BROKER],
    auto_offset_reset='earliest',
    value_deserializer=safe_json_loads
)

print(f"Listening to Kafka topic: {TOPIC}")

for msg in consumer:
    data = msg.value
    if data is None:
        print("[WARN] Received empty or invalid JSON message, skipping")
        continue
    print("Received:", data)
    message = data.get("message")
    if not message:
        print("[WARN] 'message' key missing or empty, skipping")
        continue

    try:
        cursor.execute("INSERT INTO user_logs (message) VALUES (%s)", (message,))
        conn.commit()
        print("Inserted into DB")
    except Exception as e:
        print(f"[ERROR] DB insert failed: {e}")
        conn.rollback()
