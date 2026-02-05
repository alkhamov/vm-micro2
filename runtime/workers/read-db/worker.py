import time
import requests
import psycopg2
from psycopg2.extras import RealDictCursor

CAMUNDA_URL = "http://camunda:8080/engine-rest"
TOPIC = "read-db"
WORKER_ID = "read-db-worker"

DB_CONFIG = {
    "host": "demo-postgres",
    "port": 5432,
    "dbname": "demo",
    "user": "demo_user",
    "password": "demo_pass"
}

# -------- Camunda API --------

def fetch_and_lock():
    url = f"{CAMUNDA_URL}/external-task/fetchAndLock"
    payload = {
        "workerId": WORKER_ID,
        "maxTasks": 1,
        "usePriority": True,
        "topics": [{
            "topicName": TOPIC,
            "lockDuration": 60000
        }]
    }
    r = requests.post(url, json=payload)
    r.raise_for_status()
    return r.json()

def complete_task(task_id, variables):
    url = f"{CAMUNDA_URL}/external-task/{task_id}/complete"
    payload = {
        "workerId": WORKER_ID,
        "variables": variables
    }
    r = requests.post(url, json=payload)
    r.raise_for_status()

# -------- DB Logic --------

def read_from_db(request_id: int):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        SELECT name, action
        FROM requests
        WHERE id = %s
        """,
        (request_id,)
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    return row

# -------- Main Loop --------

def main():
    print("🚀 read-db worker started")

    while True:
        tasks = fetch_and_lock()

        if not tasks:
            time.sleep(2)
            continue

        for task in tasks:
            task_id = task["id"]
            variables = task.get("variables", {})

            print(f"📥 Processing task {task_id}")

            # 1️⃣ requestId aus Prozess lesen
            if "requestId" not in variables:
                raise Exception("requestId is missing in process variables")

            request_id = variables["requestId"]["value"]

            # 2️⃣ DB lesen
            data = read_from_db(request_id)

            if data is None:
                raise Exception(f"No DB record found for requestId={request_id}")

            # 3️⃣ Variablen an Camunda zurückgeben
            result_variables = {
                "name": {"value": data["name"], "type": "String"},
                "action": {"value": data["action"], "type": "String"}
            }

            complete_task(task_id, result_variables)
            print(f"✅ Task {task_id} completed")

if __name__ == "__main__":
    main()
