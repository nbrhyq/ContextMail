from fastapi.testclient import TestClient

from app.main import app
from app.api import routes
from app.graph.workflow import ContextMailWorkflow


client = TestClient(app)
routes._workflow = ContextMailWorkflow(use_llm=False)


def test_plan_endpoint_returns_structured_decision():
    response = client.post(
        "/api/v1/runs/plan",
        json={"user_request": "Write a short thank-you email to my professor."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "OTHER"
    assert payload["agents_required"] == ["writer_agent"]
    assert payload["next_action"] == "EXECUTE"


def test_end_to_end_run_edit_and_approve_mock_action():
    created = client.post(
        "/api/v1/runs",
        json={
            "user_request": "Write a short thank-you email to my professor.",
            "recipient": {"name": "Professor Lee", "email": "lee@example.edu"},
        },
    )
    assert created.status_code == 200
    run = created.json()
    assert run["status"] == "READY_FOR_APPROVAL"

    edited = client.put(
        f"/api/v1/runs/{run['id']}/draft",
        json={
            "recipient": "lee@example.edu",
            "subject": "Thank you",
            "body": "Dear Professor Lee,\n\nThank you for your time.\n\nKind regards",
            "attachments": [],
        },
    )
    assert edited.status_code == 200

    approved = client.post(f"/api/v1/runs/{run['id']}/approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == "SENT"
    assert approved.json()["mock_message_id"].startswith("mock_email_")
