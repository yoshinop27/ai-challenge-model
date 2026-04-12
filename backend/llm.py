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


def _call_openrouter(messages: list[dict], temperature: float = 0.1) -> str:
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

    raw_confidence = raw.get("confidence")
    if not isinstance(raw_confidence, dict):
        raise ValueError("LLM response missing valid 'confidence' object")

    confidence = {k: float(raw_confidence.get(k, 0.0)) for k in LABELS}
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
    raw_text = _call_openrouter(messages)
    try:
        raw = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM returned non-JSON response: {exc}") from exc
    return _normalize(raw)


_GENERIC_CROP_PROMPT = """\
You are an expert agronomist. Given soil condition and moisture data, return structured crop recommendations.

Respond ONLY with a JSON object in this exact format:
{
  "mode": "generic",
  "summary": "<1-2 sentences describing this soil condition and moisture level and their combined effect on farming>",
  "good_crops": ["<crop>", "<crop>", "<crop>", "<crop>"],
  "avoid_crops": ["<crop>", "<crop>", "<crop>"],
  "tip": "<one concise, practical farming tip accounting for both soil condition and moisture>"
}

Be specific and practical. Do not include any other text."""

_TARGETED_CROP_PROMPT = """\
You are an expert agronomist. The farmer is considering specific crops. Evaluate each one for the given soil condition and moisture level.

Respond ONLY with a JSON object in this exact format:
{
  "mode": "targeted",
  "summary": "<1-2 sentences describing this soil condition and moisture level and their combined effect on farming>",
  "crop_analysis": [
    {"crop": "<name>", "suitable": true, "reason": "<brief reason>"},
    {"crop": "<name>", "suitable": false, "reason": "<brief reason>"}
  ],
  "tip": "<one concise, practical farming tip accounting for both soil condition and moisture>"
}

Evaluate every crop the farmer listed. Be honest and specific. Do not include any other text."""


def get_crop_recommendations(
    soil_label: str,
    confidence: float,
    crops: list[str] | None = None,
    moisture_label: str | None = None,
) -> dict:
    soil_desc = f"Soil condition: {soil_label} ({confidence:.1f}% confidence)"
    if moisture_label:
        soil_desc += f"\nSoil moisture: {moisture_label}"

    if crops:
        crop_str = ", ".join(crops)
        system = _TARGETED_CROP_PROMPT
        user = f"{soil_desc}\nCrops to evaluate: {crop_str}"
    else:
        system = _GENERIC_CROP_PROMPT
        user = soil_desc

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    raw_text = _call_openrouter(messages, temperature=0.3)
    try:
        raw = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM returned non-JSON response: {exc}") from exc

    result: dict = {
        "mode": raw.get("mode", "generic"),
        "summary": str(raw.get("summary", "")),
        "tip": str(raw.get("tip", "")),
    }
    if result["mode"] == "targeted":
        result["crop_analysis"] = [
            {
                "crop": str(item.get("crop", "")),
                "suitable": bool(item.get("suitable", False)),
                "reason": str(item.get("reason", "")),
            }
            for item in raw.get("crop_analysis", [])
            if isinstance(item, dict)
        ]
    else:
        result["good_crops"] = [str(c) for c in raw.get("good_crops", [])]
        result["avoid_crops"] = [str(c) for c in raw.get("avoid_crops", [])]
    return result
