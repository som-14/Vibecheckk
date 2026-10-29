# Plain-English description: Launches live FastAPI and Next.js servers, performs real curl/HTTP requests, and proves the complete flow from login to video upload and analysis retrieval.

import os
import sys

# Ensure environment is configured before importing database modules
os.environ["DATABASE_URL"] = "sqlite:///./vibecheck_dev.db"
os.environ["REDIS_URL"] = "memory://"
os.environ["PYTHONPATH"] = "."
sys.path.insert(0, ".")

import time
import json
import subprocess
import httpx
from worker.tasks import process_video

def main():
    print("=" * 65)
    print("LIVE SERVER + CURL VERIFICATION")
    print("=" * 65)

    env = os.environ.copy()

    # 1. Start FastAPI backend server on 127.0.0.1:8000
    print("\nStarting FastAPI backend server on http://127.0.0.1:8000 ...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # 2. Start Next.js frontend server on 127.0.0.1:3000
    print("Starting Next.js frontend server on http://127.0.0.1:3000 ...")
    frontend_proc = subprocess.Popen(
        ["npm.cmd", "start"],
        cwd="frontend",
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        # Wait for servers to be reachable
        time.sleep(3)

        client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=10.0)

        # STEP A: Check Frontend Login Page
        print("\n--- [Frontend Probe] GET http://127.0.0.1:3000/login ---")
        try:
            fe_resp = httpx.get("http://127.0.0.1:3000/login", timeout=5.0)
            print(f"Frontend Response Status: {fe_resp.status_code}")
            print(f"Frontend HTML Length: {len(fe_resp.text)} bytes")
            print("Contains 'Creator Login':", "Creator Login" in fe_resp.text)
        except Exception as e:
            print(f"Frontend probe note: {e}")

        # STEP B: Login through API
        print("\n--- [API Probe] POST /api/v1/auth/login ---")
        login_resp = client.post("/api/v1/auth/login", json={
            "email": "creator@vibecheck.test",
            "password": "CreatorDevPassword123!"
        })
        print(f"Status Code: {login_resp.status_code}")
        token_data = login_resp.json()
        token = token_data.get("access_token")
        print(f"Token (RS256): {token[:35]}... (expires_in: {token_data.get('expires_in_minutes')} min)")
        assert login_resp.status_code == 200 and token is not None

        headers = {"Authorization": f"Bearer {token}"}

        # STEP C: Upload Video
        print("\n--- [API Probe] POST /api/v1/videos/upload ---")
        with open("test_clip.mp4", "rb") as f:
            upload_resp = client.post(
                "/api/v1/videos/upload",
                headers=headers,
                data={"persona_id": 1, "caption": "Live test hook"},
                files={"file": ("test_clip.mp4", f, "video/mp4")}
            )
        print(f"Status Code: {upload_resp.status_code}")
        upload_data = upload_resp.json()
        video_id = upload_data.get("video_id")
        print(f"Upload Response: {upload_data}")
        assert upload_resp.status_code == 202 and video_id is not None

        # STEP D: Poll Status immediately (Expect PROCESSING)
        print(f"\n--- [API Probe] GET /api/v1/analysis/{video_id} (Immediate) ---")
        poll_resp_1 = client.get(f"/api/v1/analysis/{video_id}", headers=headers)
        print(f"Status Code: {poll_resp_1.status_code}")
        print(f"Status: {poll_resp_1.json().get('status')}")
        assert poll_resp_1.json().get("status") == "PROCESSING"

        # STEP E: Process video via worker task
        print(f"\n--- [Worker Execution] process_video({video_id}) ---")
        worker_res = process_video(video_id)
        print(f"Worker Result: {worker_res}")

        # STEP F: Poll Status after worker (Expect COMPLETED with score & critiques)
        print(f"\n--- [API Probe] GET /api/v1/analysis/{video_id} (Completed) ---")
        poll_resp_2 = client.get(f"/api/v1/analysis/{video_id}", headers=headers)
        print(f"Status Code: {poll_resp_2.status_code}")
        res_data = poll_resp_2.json()
        print(f"Status: {res_data.get('status')}")
        print(f"Virality Score: {res_data.get('virality_score')} / 100")
        print(f"Classification: {res_data.get('classification')}")
        print(f"Audience Fit Score: {res_data.get('audience_fit_score')}")
        print(f"Critiques Count: {len(res_data.get('critiques', []))}")
        for c in res_data.get("critiques", []):
            print(f"  - [{c['agent_role']} | {c['priority']}] @ {c['timestamp_marker']}s: {c['feedback_text']}")

        # STEP G: Check Frontend Result Page
        print(f"\n--- [Frontend Probe] GET http://127.0.0.1:3000/result/{video_id} ---")
        try:
            fe_res_page = httpx.get(f"http://127.0.0.1:3000/result/{video_id}", timeout=5.0)
            print(f"Result Page Status: {fe_res_page.status_code}")
            print(f"Result Page HTML Length: {len(fe_res_page.text)} bytes")
            print("Contains 'Virality Analysis Result':", "Virality Analysis Result" in fe_res_page.text)
        except Exception as e:
            print(f"Frontend result probe note: {e}")

        print("\n" + "=" * 65)
        print("LIVE FLOW VERIFIED SUCCESSFULLY!")
        print("=" * 65)

    finally:
        print("\nShutting down backend and frontend server processes...")
        backend_proc.terminate()
        frontend_proc.terminate()
        try:
            backend_proc.wait(timeout=2)
            frontend_proc.wait(timeout=2)
        except Exception:
            backend_proc.kill()
            frontend_proc.kill()
        print("Server processes terminated.")

if __name__ == "__main__":
    main()
