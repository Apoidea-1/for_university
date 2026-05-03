from __future__ import annotations


def test_contact_crud_and_search(client, auth_headers):
    categories_response = client.get("/api/v1/categories", headers=auth_headers)
    assert categories_response.status_code == 200
    recruiter_category = next(item for item in categories_response.json() if item["name"] == "Recruiters")

    create_response = client.post(
        "/api/v1/contacts",
        headers=auth_headers,
        json={
            "first_name": "Elena",
            "last_name": "Smirnova",
            "company": "Future HR",
            "role": "Recruiter",
            "source_where_met": "Career forum",
            "category_id": recruiter_category["id"],
            "notes": "Познакомились на карьерном форуме, говорили про стажировку.",
            "tag_names": ["internship", "career"],
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["first_name"] == "Elena"
    assert len(created["tags"]) == 2

    quick_add_response = client.post(
        "/api/v1/contacts/quick-add",
        headers=auth_headers,
        json={
            "first_name": "Maksim",
            "source_where_met": "Hackathon",
            "category_id": recruiter_category["id"],
            "notes": "Быстрое добавление после знакомства.",
        },
    )
    assert quick_add_response.status_code == 201

    list_response = client.get("/api/v1/contacts?search=internship", headers=auth_headers)
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["total"] >= 1
    assert payload["items"][0]["first_name"] == "Elena"

    update_response = client.patch(
        f"/api/v1/contacts/{created['id']}",
        headers=auth_headers,
        json={
            "company": "Future HR Lab",
            "importance_level": "high",
            "tag_names": ["internship", "career", "follow-up"],
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["company"] == "Future HR Lab"
    assert len(update_response.json()["tags"]) == 3

    delete_response = client.delete(f"/api/v1/contacts/{created['id']}", headers=auth_headers)
    assert delete_response.status_code == 204
