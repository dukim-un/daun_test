import json
import base64
from kafka import KafkaConsumer
import boto3
from botocore.client import Config

# Kafka 설정
KAFKA_BROKER = 'kafka-internal.kafka.svc.cluster.local:9092'
TOPIC_NAME = 'upload-topic'

# NCP Object Storage 정보
NCP_BUCKET_NAME = 'zcon-nipa-bucket'
NCP_ACCESS_KEY = 'HHx1JX3KpK5ndLkhyJBL'
NCP_SECRET_KEY = 'VlBpfYaW0UO4LSHLInpTGc3LgkcdUL0oRzslqHB2'
NCP_ENDPOINT = 'https://kr.object.ncloudstorage.com'  # 리전별 endpoint

# boto3 클라이언트 생성
s3_client = boto3.client(
    's3',
    aws_access_key_id=NCP_ACCESS_KEY,
    aws_secret_access_key=NCP_SECRET_KEY,
    endpoint_url=NCP_ENDPOINT,
    config=Config(signature_version='s3'),
    region_name='kr-standard'  # NCP 기본 리전명
)

def generate_text_object_name(offset):
    return f'daun/msg_{offset}.txt'

def upload_text_message(object_name: str, data: str) -> bool:
    try:
        s3_client.put_object(
            Bucket=NCP_BUCKET_NAME,
            Key=object_name,
            Body=data.encode('utf-8'),
            ContentType='text/plain'
        )
        print(f'Uploaded text message as {object_name}')
        return True
    except Exception as e:
        print(f'Upload text exception: {e}')
        return False

def upload_file(object_name: str, data: bytes) -> bool:
    try:
        s3_client.put_object(
            Bucket=NCP_BUCKET_NAME,
            Key=object_name,
            Body=data,
            ContentType='application/octet-stream'
        )
        print(f'Uploaded file as {object_name}')
        return True
    except Exception as e:
        print(f'Upload file exception: {e}')
        return False

def main():
    consumer = KafkaConsumer(
        TOPIC_NAME,
        bootstrap_servers=[KAFKA_BROKER],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='nks-object-storage-uploader',
        value_deserializer=lambda m: m.decode('utf-8'),
    )

    print(f'Start consuming from {TOPIC_NAME} at {KAFKA_BROKER}...')

    for message in consumer:
        print(f'Received message offset {message.offset}: {message.value}')
        try:
            payload = json.loads(message.value)

            if 'message' in payload:
                text = payload['message']
                object_name = generate_text_object_name(message.offset)
                if not upload_text_message(object_name, text):
                    print(f"Failed to upload text message at offset {message.offset}")

            elif 'filename' in payload and 'data' in payload:
                filename = payload['filename']
                data_base64 = payload['data']
                data = base64.b64decode(data_base64)
                object_name = f'daun/{filename}'
                if not upload_file(object_name, data):
                    print(f"Failed to upload file at offset {message.offset}")

            else:
                print(f"Unknown message format at offset {message.offset}, skipping.")

        except json.JSONDecodeError:
            print(f"Failed to decode JSON at offset {message.offset}, skipping.")
        except Exception as e:
            print(f"Error processing message at offset {message.offset}: {e}")

if __name__ == '__main__':
    main()
