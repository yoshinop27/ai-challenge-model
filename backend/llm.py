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


def _call_openrouter(messages: list, temperature: float = 0.1) -> str:
    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
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

    return body["choices"][0]["message"]["content"].strip()


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
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": f"Soil data:\n{data_text}"},
    ]
    raw = json.loads(_call_openrouter(messages))
    return _normalize(raw)


_CROP_SYSTEM_PROMPT = """\
You are an expert agronomist. Given a soil type, return structured crop recommendations.

Respond ONLY with a JSON object in this exact format:
{
  "summary": "<1-2 sentences describing this soil type and its key characteristics>",
  "good_crops": ["<crop>", "<crop>", "<crop>", "<crop>"],
  "avoid_crops": ["<crop>", "<crop>", "<crop>"],
  "tip": "<one concise, practical farming tip for this soil type>"
}

Be specific and practical. Do not include any other text."""


def get_crop_recommendations(soil_label: str, confidence: float) -> dict:
    messages = [
        {"role": "system", "content": _CROP_SYSTEM_PROMPT},
        {"role": "user", "content": f"Soil type: {soil_label} (classified with {confidence:.1f}% confidence)"},
    ]
    raw = json.loads(_call_openrouter(messages, temperature=0.3))
    return {
        "summary": str(raw.get("summary", "")),
        "good_crops": [str(c) for c in raw.get("good_crops", [])],
        "avoid_crops": [str(c) for c in raw.get("avoid_crops", [])],
        "tip": str(raw.get("tip", "")),
    }
