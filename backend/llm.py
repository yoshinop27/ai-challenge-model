import os
import csv
import io
import json
import urllib.request
import urllib.error

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL = "meta-llama/llama-3.2-3b-instruct"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

LABELS = ["bad", "average", "good"]

_SYSTEM_PROMPT = """\
You are a soil quality classifier. Given tabular soil data, classify the overall soil quality as one of: bad, average, or good.

Respond ONLY with a JSON object in this exact format:
{"label": "<bad|average|good>", "confidence": {"bad": <float>, "average": <float>, "good": <float>}}

The three confidence values must sum to 1.0. Do not include any other text."""


def _parse_csv(csv_bytes: bytes) -> str:
    text = csv_bytes.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        raise ValueError("CSV file is empty or has no data rows")
    lines = [", ".join(f"{k}: {v}" for k, v in row.items()) for row in rows[:20]]
    return "\n".join(lines)


def _call_openrouter(user_content: str) -> dict:
    payload = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.1,
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    content = body["choices"][0]["message"]["content"].strip()
    return json.loads(content)


def _normalize(raw: dict) -> dict:
    label = raw.get("label", "").lower()
    if label not in LABELS:
        raise ValueError(f"Unexpected label from LLM: {label!r}")

    confidence = {k: float(raw["confidence"].get(k, 0.0)) for k in LABELS}
    total = sum(confidence.values())
    if total > 0:
        confidence = {k: round(v / total, 6) for k, v in confidence.items()}

    return {"label": label, "confidence": confidence}


def predict_tabular(csv_bytes: bytes) -> dict:
    data_text = _parse_csv(csv_bytes)
    user_content = f"Soil data:\n{data_text}"
    raw = _call_openrouter(user_content)
    return _normalize(raw)
