"""Sağlık kontrolü ve temel bağımlılık doğrulama testleri."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_ok() -> None:
    """GET /api/health uç noktasının 200 ve beklenen JSON şemasını döndürdüğünü doğrular."""
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["app"] == "ReqSense"
    assert isinstance(payload["demo_mode"], bool)


def test_core_dependencies_importable() -> None:
    """Temel backend kütüphanelerinin sorunsuz içe aktarılabildiğini doğrular."""
    import google.genai  # noqa: F401
    import pydantic  # noqa: F401
    import sqlalchemy  # noqa: F401

    assert hasattr(google.genai, "Client")
