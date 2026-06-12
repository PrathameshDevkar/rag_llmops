def test_create_user_endpoint_success(client):
    response = client.post(
        "/users",
        json={"username": "qa_engineer", "password": "supersecretpassword"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["username"] == "qa_engineer"

def test_create_user_duplicate_conflict(client, test_user):
    # Try to insert a user with the same name as the pre-loaded fixture
    response = client.post(
        "/users",
        json={"username": test_user.username, "password": "alternativepassword"}
    )
    assert response.status_code == 409
    assert "already exist" in response.json()["detail"]