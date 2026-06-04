"""Health endpoint tests."""


def test_health_returns_200_json(client) -> None:
    """Health check endpoint returns HTTP 200 with JSON body."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
