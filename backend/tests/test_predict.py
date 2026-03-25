import io
import pytest
from PIL import Image
from httpx import AsyncClient, ASGITransport
from backend.main import app


def make_dummy_image() -> bytes:
    img = Image.new("RGB", (224, 224), color=(100, 80, 60))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def transport():
    return ASGITransport(app=app)


@pytest.mark.asyncio
async def test_predict_returns_200(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/predict",
            files={"file": ("soil.jpg", make_dummy_image(), "image/jpeg")},
        )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_predict_response_shape(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/predict",
            files={"file": ("soil.jpg", make_dummy_image(), "image/jpeg")},
        )
    data = r.json()
    assert "label" in data
    assert data["label"] in ["bad", "average", "good"]
    assert "confidence" in data
    assert set(data["confidence"].keys()) == {"bad", "average", "good"}


@pytest.mark.asyncio
async def test_predict_no_file_returns_422(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/predict")
    assert r.status_code == 422
