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
from pydantic import BaseModel  # noqa: E402
from backend.model import DualClassifier  # noqa: E402
from backend.llm import predict_tabular, get_crop_recommendations  # noqa: E402
from backend.farm_analysis import analyze_farm  # noqa: E402

app = FastAPI(title="AI Challenge API")

_classifier = DualClassifier()

_cors_origins = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=r"http://localhost:\d+",
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
    _soil = result["soil"]

    try:
        result["recommendations"] = await asyncio.to_thread(
            get_crop_recommendations,
            _soil["label"],
            _soil["confidence"][_soil["label"]] * 100,
            crop_list,
            result["moisture"]["label"],
        )
    except Exception:
        result["recommendations"] = None

    return result


class AnalyzeFarmRequest(BaseModel):
    farm: dict
    samples: list[dict]
    crops: list[str]
    satellite_b64: str | None = None
    bounds: dict | None = None


@app.post("/analyze-farm")
async def analyze_farm_endpoint(body: AnalyzeFarmRequest) -> dict:
    try:
        return await asyncio.to_thread(
            analyze_farm, body.farm, body.samples, body.crops, body.satellite_b64, body.bounds
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
