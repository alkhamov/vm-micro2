FROM python:3.11-slim

WORKDIR /app

COPY write_worker.py .

RUN pip install --no-cache-dir requests psycopg2-binary

CMD ["python", "write_worker.py"]
