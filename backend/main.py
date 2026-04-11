import asyncio
import os
from pathlib import Path


def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from backend.model import SoilClassifier  # noqa: E402
from backend.llm import predict_tabular, get_crop_recommendations  # noqa: E402

app = FastAPI(title="AI Challenge API")
_classifier = SoilClassifier()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    type: str = Form("image"),
    crops: str = Form(""),
) -> dict:
    contents = await file.read()
    crop_list = [c.strip() for c in crops.split(",") if c.strip()]

    if type == "tabular":
        try:
            return await asyncio.to_thread(predict_tabular, contents)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=str(exc))

    result = await asyncio.to_thread(_classifier.predict, contents)
    try:
        top_confidence = result["confidence"][result["label"]] * 100
        result["recommendations"] = await asyncio.to_thread(
            get_crop_recommendations, result["label"], top_confidence, crop_list
        )
    except Exception:
        result["recommendations"] = None
    return result
