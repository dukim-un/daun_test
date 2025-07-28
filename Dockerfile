FROM python:3.10-slim

WORKDIR /app2
COPY data_insert_consumer.py /app2/
RUN pip install kafka-python mysql-connector-python

CMD ["python", "data_insert_consumer.py"]
