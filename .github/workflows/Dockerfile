FROM python:3.10-slim

WORKDIR /app
COPY data_insert_consumer.py /app/
RUN pip install kafka-python mysql-connector-python

CMD ["python", "data_insert_consumer.py"]
