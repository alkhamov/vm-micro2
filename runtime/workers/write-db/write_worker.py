import time
import requests
import psycopg2

CAMUNDA_URL = "http://camunda:8080/engine-rest"
TOPIC = "write-db"
WORKER_ID = "write-db-worker"

DB_CONFIG = {
    "host": "demo-postgres",
    "port": 5432,
    "dbname": "demo",
    "user": "demo_user",
    "password": "demo_pass"
}

# ---------- Camunda REST ----------

def fetch_and_lock():
    url = f"{CAMUNDA_URL}/external-task/fetchAndLock"
    payload = {
        "workerId": WORKER_ID,
        "maxTasks": 1,
        "usePriority": True,
        "topics": [{
            "topicName": TOPIC,
            "lockDuration": 60000  # 60s lock
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

# ---------- DB ----------

def update_use_case(request_id: int, use_case: str):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE requests
        SET use_case = %s
        WHERE id = %s
        """,
        (use_case, request_id)
    )
    conn.commit()
    cur.close()
    conn.close()

# ---------- Helpers ----------

def extract_use_case(variables: dict) -> str | None:
    """
    Expected (after BPMN change to resultVariable=useCase + singleEntry):
      useCase.value == "activate"
    """
    v = variables.get("useCase")
    if not v:
        return None

    value = v.get("value")
    if isinstance(value, str) and value.strip():
        return value

    return None

# ---------- Main ----------

def main():
    print("🚀 write-db worker started")

    while True:
        try:
            tasks = fetch_and_lock()
        except Exception as e:
            print(f"❌ fetchAndLock error: {e}")
            time.sleep(3)
            continue

        if not tasks:
            time.sleep(2)
            continue

        for task in tasks:
            task_id = task["id"]
            variables = task.get("variables", {})

            print(f"📥 Processing task {task_id}")

            try:
                # requestId muss da sein (vom User Task)
                if "requestId" not in variables:
                    raise Exception("requestId is missing")

                request_id = variables["requestId"]["value"]

                # useCase aus DMN Ergebnis holen (robust)
                use_case = extract_use_case(variables)
                if not use_case:
                    raise Exception(f"useCase missing/invalid: {variables.get('useCase')}")

                # DB update
                update_use_case(int(request_id), use_case)

                # Task complete
                complete_task(task_id)
                print(f"✅ Updated request {request_id} with use_case='{use_case}'")

            except Exception as e:
                # Worker soll nicht sterben: Task als failure markieren
                print(f"❌ Task error: {e}")
                try:
                    fail_task(task_id, "write-db worker failed", str(e), retries=3, retry_timeout=15000)
                except Exception as fe:
                    print(f"❌ Could not report failure to Camunda: {fe}")

if __name__ == "__main__":
    main()
