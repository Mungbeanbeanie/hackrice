from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_chrome_extension_origin() -> None:
    origin = "chrome-extension://abcdefghijklmnopabcdefghijklmnop"
    response = client.options(
        "/api/search",
        headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
    )
    assert response.headers["access-control-allow-origin"] == origin


def test_cors_rejects_other_origins() -> None:
    response = client.options(
        "/api/search",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in response.headers
