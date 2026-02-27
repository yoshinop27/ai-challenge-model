import io
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app


@pytest.fixture
def transport():
    return ASGITransport(app=app)


@pytest.mark.asyncio
async def test_health(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_upload_single_file(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/upload",
            files={"files": ("hello.txt", io.BytesIO(b"hello world"), "text/plain")},
        )
    assert r.status_code == 200
    data = r.json()
    assert len(data["uploaded"]) == 1
    assert data["uploaded"][0]["filename"] == "hello.txt"
    assert data["uploaded"][0]["size"] == 11


@pytest.mark.asyncio
async def test_upload_multiple_files(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/upload",
            files=[
                ("files", ("a.txt", io.BytesIO(b"aaa"), "text/plain")),
                ("files", ("b.txt", io.BytesIO(b"bbbb"), "text/plain")),
            ],
        )
    assert r.status_code == 200
    data = r.json()
    assert len(data["uploaded"]) == 2
    names = {f["filename"] for f in data["uploaded"]}
    assert names == {"a.txt", "b.txt"}


@pytest.mark.asyncio
async def test_upload_no_files_returns_422(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/upload")
    assert r.status_code == 422
