"""
Full-farm crop suitability prediction using weather, elevation, ground samples,
and Claude Opus (vision-language model) via OpenRouter.
"""
import os
import io
import re
import base64
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
import numpy as np
import urllib.request
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.interpolate import RegularGridInterpolator

OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
OPENROUTER_API_KEY  = os.environ.get("OPENROUTER_API_KEY", "")
MODEL = "anthropic/claude-opus-4-6"
OPENROUTER_TIMEOUT_SEC = float(os.environ.get("OPENROUTER_TIMEOUT_SEC", "40"))

GRID_N   = 15
RENDER_N = 150
MARGIN   = 0.15

_CMAP = LinearSegmentedColormap.from_list("farm_suit", [
    (0.62, 0.04, 0.04, 1.00),
    (0.90, 0.25, 0.25, 0.80),
    (0.97, 0.60, 0.60, 0.30),
    (1.00, 1.00, 1.00, 0.04),
    (0.60, 0.92, 0.60, 0.30),
    (0.18, 0.70, 0.18, 0.80),
    (0.03, 0.38, 0.03, 1.00),
])


def _fetch_weather(lat: float, lng: float) -> str:
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lng}&appid={OPENWEATHER_API_KEY}&units=metric"
    )
    with urllib.request.urlopen(url, timeout=10) as r:
        d = json.loads(r.read())
    desc  = d.get("weather", [{}])[0].get("description", "unknown")
    main  = d.get("main", {})
    rain  = d.get("rain", {}).get("1h", 0)
    wind  = d.get("wind", {}).get("speed", "?")
    return (
        f"Conditions: {desc} | "
        f"Temp: {main.get('temp','?')}°C | "
        f"Humidity: {main.get('humidity','?')}% | "
        f"Rain 1h: {rain}mm | "
        f"Wind: {wind} m/s"
    )


def _fetch_forecast_summary(lat: float, lng: float) -> str:
    url = (
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={lat}&lon={lng}&appid={OPENWEATHER_API_KEY}&units=metric&cnt=40"
    )
    with urllib.request.urlopen(url, timeout=10) as r:
        d = json.loads(r.read())
    entries = d.get("list", [])
    if not entries:
        return "No forecast available"
    from collections import defaultdict
    days: dict = defaultdict(lambda: {"temps": [], "conds": [], "rain": 0.0})
    for entry in entries:
        day = entry["dt_txt"][:10]
        days[day]["temps"].append(entry["main"]["temp"])
        days[day]["conds"].append(entry["weather"][0]["description"])
        days[day]["rain"] += entry.get("rain", {}).get("3h", 0)
    lines = []
    for day, info in sorted(days.items()):
        lo, hi = min(info["temps"]), max(info["temps"])
        cond = max(set(info["conds"]), key=info["conds"].count)
        lines.append(f"{day}: {lo:.0f}–{hi:.0f}°C, {cond}, rain {info['rain']:.1f}mm")
    return "\n".join(lines)


def _fetch_elevation(lat_grid: np.ndarray, lng_grid: np.ndarray) -> np.ndarray:
    locations = [
        {"latitude": float(la), "longitude": float(lo)}
        for la, lo in zip(lat_grid.ravel(), lng_grid.ravel())
    ]
    payload = json.dumps({"locations": locations}).encode()
    req = urllib.request.Request(
        "https://api.open-elevation.com/api/v1/lookup",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        results = json.loads(r.read())["results"]
    elevations = np.array([pt["elevation"] for pt in results], dtype=float)
    return elevations.reshape(lat_grid.shape)


def _farm_bounds(farm: dict, n: int, bounds: dict | None = None):
    """Return (lats, lngs, lat_min, lat_max, lng_min, lng_max) for an n×n grid."""
    if bounds:
        lat_min = bounds["south"]
        lat_max = bounds["north"]
        lng_min = bounds["west"]
        lng_max = bounds["east"]
    else:
        lat, lng = farm["lat"], farm["lng"]
        half_deg = (farm["farmSize"] ** 0.5) * 0.003 * (1 + MARGIN)
        lat_min = lat - half_deg
        lat_max = lat + half_deg
        lng_min = lng - half_deg
        lng_max = lng + half_deg
    lats = np.linspace(lat_min, lat_max, n)
    lngs = np.linspace(lng_min, lng_max, n)
    return lats, lngs, lat_min, lat_max, lng_min, lng_max


def _call_claude(system: str, user_content: list | str, max_tokens: int = 4096) -> str:
    content = user_content if isinstance(user_content, list) else [{"type": "text", "text": user_content}]
    payload = json.dumps({
        "model": MODEL,
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": content},
        ],
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=OPENROUTER_TIMEOUT_SEC) as r:
        body = json.loads(r.read())
    raw = body["choices"][0]["message"]["content"].strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'\s*```$', '', raw, flags=re.MULTILINE)
    return raw.strip()


def _parse_json_with_fallback(raw: str, empty: dict) -> dict:
    try:
        return json.loads(raw)
    except Exception:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
        return empty


def _build_messages(farm, samples, crop, weather, elev_grid, lats, lngs, satellite_b64):
    system = (
        "You are an expert agronomist and soil scientist with deep knowledge of "
        "spatial crop suitability. Given farm data including satellite imagery, "
        "weather, elevation, and ground-truth soil samples, predict crop suitability "
        f"scores for a {GRID_N}×{GRID_N} spatial grid.\n\n"
        "Respond ONLY with a JSON object in this exact format:\n"
        '{"scores": [[row0col0, row0col1, ...], [row1col0, ...], ...], '
        '"summary": "<2 sentences: overall suitability for this crop on this farm>", '
        '"good_reason": "<1 sentence: why the high-scoring zones are suitable>", '
        '"poor_reason": "<1 sentence: why the low-scoring zones are less suitable>"}\n\n'
        f"The grid is {GRID_N} rows × {GRID_N} cols. "
        "Row 0 = southernmost latitude, col 0 = westernmost longitude. "
        "Each score is an integer 0–100. "
        "Make scores spatially coherent — vary them based on terrain, drainage patterns, "
        "vegetation visible in satellite imagery, proximity to good/bad sample points, "
        "and agronomic knowledge. Do not return a uniform grid."
    )

    def _fmt_sample(s):
        r = s['result']
        if r.get('soil'):
            soil_lbl = r['soil']['label']
            soil_conf = r['soil']['confidence'].get(soil_lbl, 0) * 100
            moist_lbl = r.get('moisture', {}).get('label', 'unknown')
            return (f"  ({s['lat']:.5f}, {s['lng']:.5f}): "
                    f"soil={soil_lbl} ({soil_conf:.0f}%), moisture={moist_lbl}")
        return (f"  ({s['lat']:.5f}, {s['lng']:.5f}): "
                f"quality={r.get('label','unknown')} (CSV lab data)")

    sample_lines = "\n".join(_fmt_sample(s) for s in samples)

    elev_summary = (
        f"min={elev_grid.min():.0f}m  max={elev_grid.max():.0f}m  "
        f"mean={elev_grid.mean():.0f}m  std={elev_grid.std():.1f}m"
    )

    text = (
        f"Farm center: {farm['lat']:.5f}°N, {farm['lng']:.5f}°W  |  "
        f"Size: {farm['farmSize']} acres\n"
        f"Crop: {crop}\n"
        f"Weather: {weather}\n"
        f"Elevation: {elev_summary}\n\n"
        f"Ground-truth samples ({len(samples)} points):\n{sample_lines}\n\n"
        f"Grid bounds: lat {lats[0]:.5f}→{lats[-1]:.5f}, "
        f"lng {lngs[0]:.5f}→{lngs[-1]:.5f}\n"
        "Predict the suitability grid now."
    )

    if satellite_b64:
        user_content = [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{satellite_b64}"}},
            {"type": "text", "text": "Satellite image of the farm above.\n\n" + text},
        ]
    else:
        user_content = text

    return system, user_content


def _render_contour(scores: np.ndarray, lat_min, lat_max, lng_min, lng_max) -> str:
    """Upsample scores and render topographic contour PNG, return base64."""
    n = scores.shape[0]
    idx = np.linspace(0, 1, n)
    interp = RegularGridInterpolator(
        (idx, idx), scores, method="cubic", bounds_error=False, fill_value=None
    )
    fine = np.linspace(0, 1, RENDER_N)
    R, C = np.meshgrid(fine, fine, indexing="ij")
    Z = np.clip(interp((R, C)), 0, 100)

    lngs_fine = np.linspace(lng_min, lng_max, RENDER_N)
    lats_fine = np.linspace(lat_min, lat_max, RENDER_N)
    X, Y = np.meshgrid(lngs_fine, lats_fine)

    levels = np.linspace(0, 100, 21)

    fig, ax = plt.subplots(figsize=(6, 6), dpi=150)
    fig.patch.set_alpha(0)
    ax.set_axis_off()
    ax.contourf(X, Y, Z, levels=levels, cmap=_CMAP)
    ax.contour(X, Y, Z, levels=levels[::2], colors="black", linewidths=0.25, alpha=0.20)
    plt.tight_layout(pad=0)

    buf = io.BytesIO()
    fig.savefig(buf, format="PNG", transparent=True, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


_TIMELINE_SYSTEM = """\
You are an expert agronomist specialising in Midwest US farming. Given a farm's location,
crops, current soil conditions, and the next 5-day weather forecast, generate a practical
lifecycle plan broken into sequential phases from soil preparation through post-harvest.

Respond ONLY with a valid JSON object in this exact format:
{
  "weather_outlook": "<2-3 sentences: near-term forecast and what it means for this farm right now>",
  "summary": "<2-3 sentences: overall seasonal strategy for these specific crops on this specific soil>",
  "phases": [
    {
      "phase": "<phase name, e.g. Soil Preparation, Planting, Early Growth, Mid-Season Care, Pre-Harvest, Harvest, Post-Harvest>",
      "window": "<date range, e.g. March 15 – April 30 2026>",
      "type": "<prepare|plant|fertilize|irrigate|spray|monitor|harvest|other>",
      "because": "<1-2 sentences explaining WHY this timing — directly reference the farm's soil type, moisture level, and forecast conditions>",
      "actions": ["<specific action 1>", "<specific action 2>", "<specific action 3>"]
    }
  ]
}

Generate 6-8 sequential phases covering the full growing season in chronological order.
Every phase MUST have a 'because' field that references the actual soil conditions and weather.
Be specific: name the soil type, cite the moisture reading, reference the forecast.
Do not include any text outside the JSON object."""


def get_farm_timeline(
    farm: dict,
    samples: list,
    crops: list,
    forecast_summary: str,
    current_weather: str,
) -> dict:
    def _fmt_sample_summary(s):
        r = s['result']
        if r.get('soil'):
            return f"{r['soil']['label']} ({r.get('moisture', {}).get('label', 'unknown')})"
        return f"quality={r.get('label', 'unknown')} (CSV)"

    soil_summary = ", ".join(_fmt_sample_summary(s) for s in samples) or "no samples"

    user_text = (
        f"Farm: {farm['lat']:.4f}°N, {farm['lng']:.4f}°W | {farm['farmSize']} acres | Iowa, USA\n"
        f"Crops: {', '.join(crops) if crops else 'unspecified'}\n"
        f"Soil samples: {soil_summary}\n"
        f"Current weather: {current_weather}\n\n"
        f"5-day forecast:\n{forecast_summary}\n\n"
        "Generate the 12-month agricultural timeline now."
    )

    raw = _call_claude(_TIMELINE_SYSTEM, user_text, max_tokens=5000)
    return _parse_json_with_fallback(raw, {"weather_outlook": "", "summary": "", "phases": []})


def _sample_crop_score(sample: dict, crop: str) -> float:
    result = sample.get("result", {})
    recommendations = result.get("recommendations") or {}
    if recommendations.get("mode") == "targeted":
        for item in recommendations.get("crop_analysis", []):
            if str(item.get("crop", "")).strip().lower() == crop.lower():
                return float(item.get("score", 50))

    if not result.get("soil"):
        return {"bad": 25.0, "average": 50.0, "good": 75.0}.get(
            str(result.get("label", "")).lower(), 50.0
        )

    soil_label = str(result.get("soil", {}).get("label", "")).lower()
    moisture_label = str(result.get("moisture", {}).get("label", "")).lower()
    score = 55.0

    if "loam" in soil_label or "alluvial" in soil_label or "black" in soil_label:
        score += 10
    if "clay" in soil_label:
        score -= 6
    if "red" in soil_label:
        score -= 4

    if moisture_label in {"moist", "moderate"}:
        score += 10
    elif moisture_label == "wet":
        score -= 6
    elif moisture_label == "dry":
        score -= 10

    return float(np.clip(score, 0, 100))


def _fallback_scores(samples: list[dict], crop: str, lats: np.ndarray, lngs: np.ndarray) -> np.ndarray:
    if not samples:
        return np.full((GRID_N, GRID_N), 50.0, dtype=float)

    lat_grid, lng_grid = np.meshgrid(lats, lngs, indexing="ij")
    weighted_scores = np.zeros((GRID_N, GRID_N), dtype=float)
    total_weights = np.zeros((GRID_N, GRID_N), dtype=float)

    for sample in samples:
        sample_lat = float(sample["lat"])
        sample_lng = float(sample["lng"])
        base_score = _sample_crop_score(sample, crop)
        dist_sq = (lat_grid - sample_lat) ** 2 + (lng_grid - sample_lng) ** 2
        weights = 1.0 / np.maximum(dist_sq, 1e-8)
        weighted_scores += base_score * weights
        total_weights += weights

    return np.clip(weighted_scores / total_weights, 0, 100)


def _fallback_crop_text(crop: str, scores: np.ndarray, samples: list[dict]) -> tuple[str, str, str]:
    avg = float(np.mean(scores))
    moisture_labels = [
        str(sample.get("result", {}).get("moisture", {}).get("label", "")).lower()
        for sample in samples
        if sample.get("result", {}).get("moisture")
    ]
    dominant_moisture = max(set(moisture_labels), key=moisture_labels.count) if moisture_labels else "mixed"

    summary = (
        f"Fallback analysis for {crop}: current sample patterns indicate an average suitability of "
        f"{avg:.0f}/100 across the farm, with {dominant_moisture} conditions driving most of the variation."
    )
    good_reason = (
        "Higher-scoring zones are closest to the strongest sample readings and inherit the most favorable "
        "soil and moisture conditions observed on the farm."
    )
    poor_reason = (
        "Lower-scoring zones are anchored by weaker nearby sample readings, so they should be validated with "
        "additional sampling before planting decisions are finalized."
    )
    return summary, good_reason, poor_reason


def _fallback_timeline(farm: dict, crops: list[str], current_weather: str) -> dict:
    start = date.today()
    crop_text = ", ".join(crops) if crops else "selected crops"
    phases = [
        ("Soil Preparation", "prepare", 0, 21, [
            "Validate low-scoring zones with another soil sample",
            "Break up compaction and improve drainage where moisture has been high",
            f"Finalize field plan for {crop_text}",
        ]),
        ("Planting Window", "plant", 21, 45, [
            "Plant the strongest zones first",
            "Delay planting in weak or saturated areas until field conditions stabilize",
            "Keep seed depth and spacing consistent across sampled zones",
        ]),
        ("Early Growth", "monitor", 45, 75, [
            "Scout emergence differences between strong and weak zones",
            "Watch for water stress or ponding in low-performing areas",
            "Use the map to target follow-up field checks",
        ]),
        ("Nutrient Management", "fertilize", 75, 110, [
            "Apply inputs conservatively in poor zones until they are verified",
            "Favor variable-rate decisions where sample quality diverges",
            "Track whether crop vigor matches the suitability map",
        ]),
        ("Mid-Season Care", "monitor", 110, 150, [
            "Monitor disease pressure in wetter sections of the farm",
            "Inspect drainage and stand health after rain events",
            "Capture more samples if field conditions shift materially",
        ]),
        ("Harvest Planning", "harvest", 150, 210, [
            "Prioritize higher-suitability areas for yield comparison",
            "Record weak zones that underperform for next season adjustments",
            "Use harvest outcomes to refine future sampling density",
        ]),
    ]

    return {
        "weather_outlook": f"Fallback timeline generated from current conditions. Current weather context: {current_weather}",
        "summary": (
            f"This plan uses the farm's sampled soil and moisture patterns to stage {crop_text} work in a practical order "
            "even when live external planning services are unavailable."
        ),
        "phases": [
            {
                "phase": name,
                "window": f"{(start + timedelta(days=start_offset)).strftime('%B %d, %Y')} – {(start + timedelta(days=end_offset)).strftime('%B %d, %Y')}",
                "type": phase_type,
                "because": "This phase prioritizes actions around the sampled soil and moisture variation already observed on the farm.",
                "actions": actions,
            }
            for name, phase_type, start_offset, end_offset, actions in phases
        ],
    }


def _analyze_crop(crop, farm, samples, weather, elev_grid, lats, lngs, satellite_b64, lat_min, lat_max, lng_min, lng_max):
    raw = ""
    try:
        system, user_content = _build_messages(
            farm, samples, crop, weather, elev_grid, lats, lngs, satellite_b64
        )
        raw = _call_claude(system, user_content)
        parsed = json.loads(raw)
    except Exception:
        parsed = _parse_json_with_fallback(raw, {})

    raw_scores = parsed.get("scores")
    try:
        scores = np.clip(np.array(raw_scores, dtype=float), 0, 100)
        if scores.shape != (GRID_N, GRID_N):
            raise ValueError("Invalid score grid shape")
    except Exception:
        scores = _fallback_scores(samples, crop, lats, lngs)

    summary, good_reason, poor_reason = _fallback_crop_text(crop, scores, samples)
    image_b64 = _render_contour(scores, lat_min, lat_max, lng_min, lng_max)

    return crop, {
        "image": image_b64,
        "coordinates": [
            [lng_min, lat_max],
            [lng_max, lat_max],
            [lng_max, lat_min],
            [lng_min, lat_min],
        ],
        "scores": scores.tolist(),
        "avg_score": float(np.mean(scores)),
        "summary": parsed.get("summary") or summary,
        "good_reason": parsed.get("good_reason") or good_reason,
        "poor_reason": parsed.get("poor_reason") or poor_reason,
    }


def analyze_farm(farm: dict, samples: list, crops: list, satellite_b64: str | None = None, bounds: dict | None = None) -> dict:
    """
    Returns {crop: {"image": base64_png, "coordinates": [[lng,lat]×4]}}
    """
    lats, lngs, lat_min, lat_max, lng_min, lng_max = _farm_bounds(farm, GRID_N, bounds)
    LAT_GRID, LNG_GRID = np.meshgrid(lats, lngs, indexing="ij")

    lat, lng = farm["lat"], farm["lng"]
    with ThreadPoolExecutor(max_workers=3) as ex:
        f_weather  = ex.submit(_fetch_weather, lat, lng)
        f_forecast = ex.submit(_fetch_forecast_summary, lat, lng)
        f_elev     = ex.submit(_fetch_elevation, LAT_GRID, LNG_GRID)

        try:
            weather = f_weather.result()
        except Exception:
            weather = "Weather data unavailable"

        try:
            forecast = f_forecast.result()
        except Exception:
            forecast = "Forecast data unavailable"

        try:
            elev_grid = f_elev.result()
        except Exception:
            elev_grid = np.zeros((GRID_N, GRID_N))

    result = {}
    with ThreadPoolExecutor(max_workers=len(crops) or 1) as ex:
        futures = {
            ex.submit(_analyze_crop, crop, farm, samples, weather, elev_grid, lats, lngs, satellite_b64, lat_min, lat_max, lng_min, lng_max): crop
            for crop in crops
        }
        for future in as_completed(futures):
            crop_name, crop_data = future.result()
            result[crop_name] = crop_data

    try:
        timeline = get_farm_timeline(farm, samples, crops, forecast, weather)
        if not timeline.get("phases"):
            raise ValueError("Timeline did not contain phases")
        result["__timeline__"] = timeline
    except Exception:
        result["__timeline__"] = _fallback_timeline(farm, crops, weather)

    return result
