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

# -------- Camunda API --------

def fetch_and_lock():
    url = f"{CAMUNDA_URL}/external-task/fetchAndLock"
    payload = {
        "workerId": WORKER_ID,
        "maxTasks": 1,
        "usePriority": True,
        "topics": [{
            "topicName": TOPIC,
            "lockDuration": 10000
        }]
    }
    r = requests.post(url, json=payload)
    r.raise_for_status()
    return r.json()

def complete_task(task_id):
    url = f"{CAMUNDA_URL}/external-task/{task_id}/complete"
    payload = {
        "workerId": WORKER_ID
    }
    r = requests.post(url, json=payload)
    r.raise_for_status()

# -------- DB Logic --------

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

# -------- Main Loop --------

def main():
    print("🚀 write-db worker started")

    while True:
        tasks = fetch_and_lock()

        if not tasks:
            time.sleep(2)
            continue

        for task in tasks:
            task_id = task["id"]
            variables = task.get("variables", {})

            print(f"📥 Processing task {task_id}")

            # 1️⃣ Pflicht-Variablen prüfen
            if "requestId" not in variables:
                raise Exception("requestId is missing")

            if "useCaseResult" not in variables:
                raise Exception("useCaseResult is missing")

            request_id = variables["requestId"]["value"]

            # DMN: singleResult → Objekt → Feld "useCase"
            use_case = variables["useCaseResult"]["value"]["useCase"]

            # 2️⃣ DB Update
            update_use_case(request_id, use_case)

            # 3️⃣ Task abschließen
            complete_task(task_id)
            print(f"✅ Updated request {request_id} with use_case='{use_case}'")

if __name__ == "__main__":
    main()
