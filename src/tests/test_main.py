import os
from fastapi.testclient import TestClient
from src.api.main import app,
import tempfile

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"info": "WhisperX API"}


def test_create_transcription_job():
    files = {"file": open("/home/namastex/whisperx-api/data/test.mp4", "rb")}
    response = client.post(
        "/jobs", files=files
    )
    assert response.status_code == 200
    assert "task_id" in response.json()
    assert response.json()["status"] == "PENDING"


def test_list_jobs():
    response = client.get("/jobs")
    assert response.status_code == 200


def test_get_job_status():
    files = {"file": open("/home/namastex/whisperx-api/data/test.mp4", "rb")}
    create_response = client.post(
        "/jobs", files=files
    )
    task_id = create_response.json()["task_id"]

    response = client.get(
        f"/jobs/{task_id}"
    )
    assert response.status_code == 200


def test_stop_job():
    files = {"file": open("/home/namastex/whisperx-api/data/test.mp4", "rb")}
    create_response = client.post(
        "/jobs", files=files
    )
    task_id = create_response.json()["task_id"]

    response = client.post(
        f"/jobs/{task_id}/stop"
    )
    assert response.status_code == 200
    assert response.json()["status"] == "STOPPED"
