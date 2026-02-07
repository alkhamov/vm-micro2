import os
import time
import random
import requests
import psycopg2

CAMUNDA_URL = os.getenv("CAMUNDA_URL", "http://camunda:8080/engine-rest")
TOPIC = os.getenv("TOPIC", "write-db")
WORKER_ID = os.getenv("WORKER_ID", "write-db-worker")
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
            # WICHTIG: Variablen explizit anfordern
            "variables": ["requestId", "useCase"]
        }]
    }
    r = requests.post(url, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()

def complete_task(task_id):
    url = f"{CAMUNDA_URL}/external-task/{task_id}/complete"
    payload = {"workerId": WORKER_ID}
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

def update_use_case(request_id: int, use_case: str):
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE requests
                SET use_case = %s
                WHERE id = %s
                """,
                (use_case, request_id)
            )
        conn.commit()
    finally:
        conn.close()

def extract_use_case(variables: dict) -> str | None:
    # Expected: useCase.value == "activate"
    v = variables.get("useCase")
    if not v or "value" not in v:
        return None
    value = v.get("value")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None

def main():
    print("🚀 write-db worker started")

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
                req_var = variables.get("requestId")
                if not req_var or "value" not in req_var:
                    raise Exception(f"requestId is missing. variables={variables}")
                request_id = int(req_var["value"])

                use_case = extract_use_case(variables)
                if not use_case:
                    raise Exception(f"useCase missing/invalid: {variables.get('useCase')}")

                update_use_case(request_id, use_case)
                complete_task(task_id)
                print(f"✅ Updated requestId={request_id} use_case='{use_case}'")

            except Exception as e:
                print(f"❌ Task error: {e}")
                try:
                    fail_task(task_id, "write-db worker failed", str(e), retries=3, retry_timeout=15000)
                except Exception as fe:
                    print(f"❌ Could not report failure: {fe}")

if __name__ == "__main__":
    main()
