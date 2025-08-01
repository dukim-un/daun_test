FROM python:3.10-slim

WORKDIR /app
COPY object_upload_all.py /app/
RUN pip install kafka-python boto3

CMD ["python", "object_upload_all.py"]
