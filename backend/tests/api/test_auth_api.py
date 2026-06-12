def test_login_success(client, test_user):
    response = client.post(
        "/auth/login",
        json={"username": test_user.username, "password": "test_user123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client, test_user):
    response = client.post(
        "/auth/login",
        json={"username": test_user.username, "password": "incorrectpassword"}
    )
    print(f"==================response is============={response}")
    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]

def test_login_missing_user(client):
    response = client.post(
        "/auth/login",
        json={"username": "non_existent_user", "password": "some_password"}
    )
    assert response.status_code == 401