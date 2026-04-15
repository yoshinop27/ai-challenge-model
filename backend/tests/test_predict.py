import io
from PIL import Image
from fastapi.testclient import TestClient

from backend.main import app


def make_dummy_image() -> bytes:
    img = Image.new("RGB", (224, 224), color=(100, 80, 60))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def test_predict_returns_200(monkeypatch):
    monkeypatch.setattr(
        "backend.main.get_crop_recommendations",
        lambda *args, **kwargs: {"mode": "generic", "summary": "", "tip": "", "good_crops": [], "avoid_crops": []},
    )
    client = TestClient(app)
    r = client.post(
        "/predict",
        files={"file": ("soil.jpg", make_dummy_image(), "image/jpeg")},
    )
    assert r.status_code == 200


def test_predict_response_shape(monkeypatch):
    monkeypatch.setattr(
        "backend.main.get_crop_recommendations",
        lambda *args, **kwargs: {"mode": "generic", "summary": "", "tip": "", "good_crops": [], "avoid_crops": []},
    )
    client = TestClient(app)
    r = client.post(
        "/predict",
        files={"file": ("soil.jpg", make_dummy_image(), "image/jpeg")},
    )
    data = r.json()
    assert "soil" in data
    assert "moisture" in data
    assert "label" in data["soil"]
    assert "confidence" in data["soil"]
    assert data["soil"]["label"] in data["soil"]["confidence"]
    assert "label" in data["moisture"]
    assert "confidence" in data["moisture"]
    assert data["moisture"]["label"] in data["moisture"]["confidence"]
    assert "recommendations" in data


def test_predict_no_file_returns_422():
    client = TestClient(app)
    r = client.post("/predict")
    assert r.status_code == 422
