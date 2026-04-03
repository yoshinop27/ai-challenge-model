import os
from pathlib import Path

# Load .env from project root before importing modules that read env vars
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.is_file():
    for _line in _env_path.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.model import SoilClassifier
from backend.llm import predict_tabular

app = FastAPI(title="AI Challenge API")
_classifier = SoilClassifier()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    type: str = Form("image"),
):
    contents = await file.read()

    if type == "tabular":
        try:
            return predict_tabular(contents)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=str(exc))

    return _classifier.predict(contents)
