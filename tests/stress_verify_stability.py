import os
import sys
import time
import concurrent.futures
import requests

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from security import create_access_token

BASE_URL = "http://127.0.0.1:8000/api"

TOKEN_U1 = create_access_token({"sub": "1", "email": "rahul.verma@example.com"})
TOKEN_U2 = create_access_token({"sub": "2", "email": "priya.sharma@example.com"})

def get_headers(user_id):
    tok = TOKEN_U1 if user_id == 1 else TOKEN_U2
    return {"Authorization": f"Bearer {tok}"}

def check_health():
    res = requests.get(f"{BASE_URL}/health", timeout=5)
    return res.status_code == 200

def test_rag_and_assistant(user_id=1, report_id=1):
    payload = {
        "message": f"What are the surgical travel guidelines for coronary artery disease? Query time: {time.time()}",
        "conversation_id": None,
        "report_id": report_id,
        "hospital_id": 1
    }
    res = requests.post(
        f"{BASE_URL}/services/chat?user_id={user_id}&report_id={report_id}",
        json=payload,
        headers=get_headers(user_id),
        timeout=30
    )
    return res.status_code == 200

def test_report_analysis(user_id=1, report_id=1):
    res = requests.get(f"{BASE_URL}/reports/{report_id}", headers=get_headers(user_id), timeout=5)
    return res.status_code == 200

def test_hospital_recommendations(user_id=1):
    params = {
        "specialty": "Cardiology",
        "city": "Hyderabad",
        "priority_mode": "balanced",
        "user_id": user_id
    }
    res = requests.get(f"{BASE_URL}/recommend/hospitals", params=params, headers=get_headers(user_id), timeout=10)
    return res.status_code == 200

def test_cost_and_recovery(user_id=1, report_id=1):
    payload = {
        "treatment_name": "Coronary Angioplasty (PTCA)",
        "city": "Hyderabad",
        "user_id": user_id,
        "report_id": report_id,
        "has_diabetes": True,
        "has_hypertension": True
    }
    r1 = requests.post(f"{BASE_URL}/cost/predict", json=payload, headers=get_headers(user_id), timeout=10)
    r2 = requests.post(f"{BASE_URL}/cost/recovery-timeline", json=payload, headers=get_headers(user_id), timeout=15)
    return r1.status_code == 200 and r2.status_code == 200

def test_medical_travel():
    payload = {
        "origin": "MG Road, Bangalore",
        "destination": "Apollo Hospital, Bannerghatta Road, Bangalore",
        "travel_mode": "car"
    }
    r1 = requests.post(f"{BASE_URL}/travel/route", json=payload, timeout=10)
    r2 = requests.get(f"{BASE_URL}/travel/nearby?location=Apollo+Hospital+Bangalore&category=hotel&limit=3", timeout=10)
    r3 = requests.get(f"{BASE_URL}/travel/emergency?city=Bangalore", timeout=10)
    return r1.status_code == 200 and r2.status_code == 200 and r3.status_code == 200

def run_concurrent_stress(rounds=15, workers=5):
    print(f"Starting concurrent multi-threaded stress test: {rounds} tasks across {workers} workers...")
    start_time = time.time()
    
    tasks = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        for i in range(rounds):
            uid = 1 if (i % 2 == 0) else 2
            rid = 1 if uid == 1 else 24  # Report 1 belongs to user 1, Report 24 belongs to user 2
            tasks.append(executor.submit(test_rag_and_assistant, uid, rid))
            tasks.append(executor.submit(test_report_analysis, uid, rid))
            tasks.append(executor.submit(test_hospital_recommendations, uid))
            tasks.append(executor.submit(test_cost_and_recovery, uid, rid))
            tasks.append(executor.submit(test_medical_travel))

        results = [t.result() for t in concurrent.futures.as_completed(tasks)]
    
    elapsed = time.time() - start_time
    success_count = sum(1 for r in results if r)
    total_ops = len(results)
    print(f"Stress test finished in {elapsed:.2f}s: {success_count}/{total_ops} operations succeeded.")
    assert success_count == total_ops, f"Failed operations: {total_ops - success_count}"

if __name__ == "__main__":
    assert check_health(), "Backend is not healthy!"
    run_concurrent_stress(rounds=10, workers=4)
    print("ALL CONCURRENT MULTI-THREADED OPERATIONS PASSED CLEANLY.")
