"""
Full-farm crop suitability prediction using weather, elevation, ground samples,
and Claude Opus (vision-language model) via OpenRouter.
"""
import os
import io
import re
import base64
import json
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

GRID_N   = 15   # Claude predicts a 15×15 score grid
RENDER_N = 150  # Upsampled to 150×150 for smooth PNG output
MARGIN   = 0.15 # Fractional padding around farm bounds

# Diverging red→transparent→green colormap.
# Score 0   = dark red,   fully opaque   (confident: bad)
# Score 50  = transparent white          (uncertain: satellite shows through)
# Score 100 = dark green, fully opaque   (confident: good)
# Alpha varies with distance from 50 so uncertain areas fade away.
_CMAP = LinearSegmentedColormap.from_list("farm_suit", [
    (0.62, 0.04, 0.04, 1.00),  # score   0 – dark red, solid
    (0.90, 0.25, 0.25, 0.80),  # score  17
    (0.97, 0.60, 0.60, 0.30),  # score  33 – light red, fading
    (1.00, 1.00, 1.00, 0.04),  # score  50 – nearly transparent
    (0.60, 0.92, 0.60, 0.30),  # score  67 – light green, fading
    (0.18, 0.70, 0.18, 0.80),  # score  83
    (0.03, 0.38, 0.03, 1.00),  # score 100 – dark green, solid
])


# ── Data fetching ────────────────────────────────────────────────────────────

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


# ── Grid bounds ──────────────────────────────────────────────────────────────

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


# ── Claude call ──────────────────────────────────────────────────────────────

def _call_claude(system: str, user_content: list | str) -> str:
    content = user_content if isinstance(user_content, list) else [{"type": "text", "text": user_content}]
    payload = json.dumps({
        "model": MODEL,
        "max_tokens": 2048,
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
    with urllib.request.urlopen(req, timeout=90) as r:
        body = json.loads(r.read())
    return body["choices"][0]["message"]["content"].strip()


def _build_messages(farm, samples, crop, weather, elev_grid, lats, lngs, satellite_b64):
    system = (
        "You are an expert agronomist and soil scientist with deep knowledge of "
        "spatial crop suitability. Given farm data including satellite imagery, "
        "weather, elevation, and ground-truth soil samples, predict crop suitability "
        f"scores for a {GRID_N}×{GRID_N} spatial grid.\n\n"
        "Respond ONLY with a JSON object in this exact format:\n"
        '{"scores": [[row0col0, row0col1, ...], [row1col0, ...], ...]}\n\n'
        f"The grid is {GRID_N} rows × {GRID_N} cols. "
        "Row 0 = southernmost latitude, col 0 = westernmost longitude. "
        "Each score is an integer 0–100. "
        "Make scores spatially coherent — vary them based on terrain, drainage patterns, "
        "vegetation visible in satellite imagery, proximity to good/bad sample points, "
        "and agronomic knowledge. Do not return a uniform grid."
    )

    sample_lines = "\n".join(
        f"  ({s['lat']:.5f}, {s['lng']:.5f}): "
        f"soil={s['result']['soil']['label']} "
        f"({s['result']['soil']['confidence'].get(s['result']['soil']['label'], 0)*100:.0f}%), "
        f"moisture={s['result']['moisture']['label']} "
        f"({s['result']['moisture']['confidence'].get(s['result']['moisture']['label'], 0)*100:.0f}%)"
        for s in samples
    )

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


# ── Contour rendering ────────────────────────────────────────────────────────

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


# ── Public entry point ───────────────────────────────────────────────────────

def analyze_farm(farm: dict, samples: list, crops: list, satellite_b64: str | None = None, bounds: dict | None = None) -> dict:
    """
    Returns {crop: {"image": base64_png, "coordinates": [[lng,lat]×4]}}
    """
    lats, lngs, lat_min, lat_max, lng_min, lng_max = _farm_bounds(farm, GRID_N, bounds)
    LAT_GRID, LNG_GRID = np.meshgrid(lats, lngs, indexing="ij")

    try:
        weather = _fetch_weather(farm["lat"], farm["lng"])
    except Exception:
        weather = "Weather data unavailable"

    try:
        elev_grid = _fetch_elevation(LAT_GRID, LNG_GRID)
    except Exception:
        elev_grid = np.zeros((GRID_N, GRID_N))

    result = {}
    for crop in crops:
        system, user_content = _build_messages(
            farm, samples, crop, weather, elev_grid, lats, lngs, satellite_b64
        )
        raw = _call_claude(system, user_content)

        try:
            scores = np.array(json.loads(raw)["scores"], dtype=float)
        except Exception:
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            scores = np.array(json.loads(match.group())["scores"], dtype=float) if match \
                else np.full((GRID_N, GRID_N), 50.0)

        scores = np.clip(scores, 0, 100)
        image_b64 = _render_contour(scores, lat_min, lat_max, lng_min, lng_max)

        result[crop] = {
            "image": image_b64,
            "coordinates": [
                [lng_min, lat_max],
                [lng_max, lat_max],
                [lng_max, lat_min],
                [lng_min, lat_min],
            ],
        }

    return result
