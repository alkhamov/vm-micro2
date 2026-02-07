import os
import time
import random
import requests
import psycopg2
from psycopg2.extras import RealDictCursor

CAMUNDA_URL = os.getenv("CAMUNDA_URL", "http://camunda:8080/engine-rest")
TOPIC = os.getenv("TOPIC", "read-db")
WORKER_ID = os.getenv("WORKER_ID", "read-db-worker")
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "5"))

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "demo-postgres"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "demo"),
    "user": os.getenv("DB_USER", "demo_user"),
    "password": os.getenv("DB_PASSWORD", "demo_pass"),
}

def fetch_and_lock():
    url = f"{CAMUNDA_URL}/external-task/fetchAndLock"
    payload = {
        "workerId": WORKER_ID,
        "maxTasks": 1,
        "usePriority": True,
        "topics": [{
            "topicName": TOPIC,
            "lockDuration": 60000,
            # requestId explizit anfordern
            "variables": ["requestId"]
        }]
    }
    r = requests.post(url, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()

def complete_task(task_id, variables):
    url = f"{CAMUNDA_URL}/external-task/{task_id}/complete"
    payload = {
        "workerId": WORKER_ID,
        "variables": variables
    }
    r = requests.post(url, json=payload, timeout=15)
    if r.status_code >= 400:
        print(f"❌ Complete failed ({r.status_code}): {r.text}")
    r.raise_for_status()

def fail_task(task_id, error_message, error_details, retries=3, retry_timeout=15000):
    url = f"{CAMUNDA_URL}/external-task/{task_id}/failure"
    payload = {
        "workerId": WORKER_ID,
        "errorMessage": error_message,
        "errorDetails": error_details,
        "retries": retries,
        "retryTimeout": retry_timeout
    }
    r = requests.post(url, json=payload, timeout=15)
    if r.status_code >= 400:
        print(f"❌ Failure report failed ({r.status_code}): {r.text}")
    r.raise_for_status()

def read_from_db(request_id: int):
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT name, action
                FROM requests
                WHERE id = %s
                """,
                (request_id,)
            )
            return cur.fetchone()
    finally:
        conn.close()

def main():
    print("🚀 read-db worker started")

    while True:
        try:
            tasks = fetch_and_lock()
        except Exception as e:
            print(f"❌ fetchAndLock error: {e}")
            time.sleep(min(30, POLL_SECONDS + random.randint(0, 3)))
            continue

        if not tasks:
            time.sleep(POLL_SECONDS)
            continue

        for task in tasks:
            task_id = task["id"]
            variables = task.get("variables", {})
            print(f"📥 Processing task {task_id}")

            try:
                v = variables.get("requestId")
                if not v or "value" not in v:
                    raise Exception(f"requestId missing. variables={variables}")

                request_id = int(v["value"])

                row = read_from_db(request_id)
                if row is None:
                    raise Exception(f"No DB record found for requestId={request_id}")

                result_variables = {
                    "name": {"value": row["name"], "type": "String"},
                    "action": {"value": row["action"], "type": "String"},
                }

                complete_task(task_id, result_variables)
                print(f"✅ Completed read-db for requestId={request_id}")

            except Exception as e:
                print(f"❌ Task error: {e}")
                try:
                    fail_task(task_id, "read-db worker failed", str(e), retries=3, retry_timeout=15000)
                except Exception as fe:
                    print(f"❌ Could not report failure: {fe}")

if __name__ == "__main__":
    main()
