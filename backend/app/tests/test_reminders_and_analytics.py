from __future__ import annotations

from datetime import datetime, timedelta


def _create_contact(client, auth_headers):
    categories_response = client.get("/api/v1/categories", headers=auth_headers)
    category_id = categories_response.json()[0]["id"]
    response = client.post(
        "/api/v1/contacts",
        headers=auth_headers,
        json={
            "first_name": "Nina",
            "company": "Scale PM",
            "category_id": category_id,
            "notes": "Product contact from meetup.",
        },
    )
    return response.json()


def test_reminder_filters_analytics_and_ai(client, auth_headers):
    contact = _create_contact(client, auth_headers)

    interaction_response = client.post(
        f"/api/v1/contacts/{contact['id']}/interactions",
        headers=auth_headers,
        json={
            "type": "meeting",
            "title": "Intro call",
            "description": "Discussed product mentorship.",
            "interaction_date": (datetime.utcnow() - timedelta(days=2)).isoformat(),
        },
    )
    assert interaction_response.status_code == 201

    active_reminder = client.post(
        "/api/v1/reminders",
        headers=auth_headers,
        json={
            "contact_id": contact["id"],
            "title": "Send follow-up",
            "description": "Share CV and thank-you note.",
            "due_date": (datetime.utcnow() + timedelta(days=2)).isoformat(),
            "reminder_type": "follow_up",
        },
    )
    assert active_reminder.status_code == 201

    overdue_reminder = client.post(
        "/api/v1/reminders",
        headers=auth_headers,
        json={
            "contact_id": contact["id"],
            "title": "Missed reminder",
            "description": "Should already be overdue.",
            "due_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "reminder_type": "follow_up",
        },
    )
    assert overdue_reminder.status_code == 201

    completed_response = client.patch(
        f"/api/v1/reminders/{active_reminder.json()['id']}",
        headers=auth_headers,
        json={"status": "completed"},
    )
    assert completed_response.status_code == 200

    overdue_list = client.get("/api/v1/reminders?status=overdue", headers=auth_headers)
    assert overdue_list.status_code == 200
    assert len(overdue_list.json()) == 1

    completed_list = client.get("/api/v1/reminders?status=completed", headers=auth_headers)
    assert completed_list.status_code == 200
    assert len(completed_list.json()) == 1

    ai_response = client.post(
        "/api/v1/ai/suggest-contact-metadata",
        headers=auth_headers,
        json={
            "notes": "Познакомились на карьерном форуме, работает в HR, обсуждали стажировку",
            "contact_id": contact["id"],
        },
    )
    assert ai_response.status_code == 200
    assert ai_response.json()["category"] == "Recruiters"

    overview = client.get("/api/v1/analytics/overview", headers=auth_headers)
    assert overview.status_code == 200
    overview_payload = overview.json()
    assert overview_payload["new_contacts_7d"] >= 1
    assert overview_payload["interactions_7d"] >= 1
    assert overview_payload["overdue_reminders"] == 1

    categories = client.get("/api/v1/analytics/categories", headers=auth_headers)
    assert categories.status_code == 200
    assert len(categories.json()) >= 1

    stale_contacts = client.get("/api/v1/analytics/stale-contacts?days=1", headers=auth_headers)
    assert stale_contacts.status_code == 200
