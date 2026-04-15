import io
import base64
import numpy as np
from PIL import Image
from scipy.interpolate import CloughTocher2DInterpolator
from matplotlib.colors import LinearSegmentedColormap

_MARGIN = 0.1
_GRID_SIZE = 200

_CMAP = LinearSegmentedColormap.from_list(
    'soil_suitability',
    [(0.82, 0.84, 0.86), (0.53, 0.94, 0.67), (0.08, 0.50, 0.24)],
)


def _interpolate(lngs: np.ndarray, lats: np.ndarray, scores: np.ndarray):
    lng_range = (lngs.max() - lngs.min()) or 0.001
    lat_range = (lats.max() - lats.min()) or 0.001
    xi = np.linspace(lngs.min() - lng_range * _MARGIN, lngs.max() + lng_range * _MARGIN, _GRID_SIZE)
    yi = np.linspace(lats.min() - lat_range * _MARGIN, lats.max() + lat_range * _MARGIN, _GRID_SIZE)
    X, Y = np.meshgrid(xi, yi)
    interp = CloughTocher2DInterpolator(
        np.column_stack([lngs, lats]), scores, fill_value=np.nan
    )
    Z = interp(np.column_stack([X.ravel(), Y.ravel()])).reshape(X.shape)
    return xi, yi, Z


def _to_raster(Z: np.ndarray) -> str:
    """Convert interpolated grid to RGBA PNG (NaN = transparent), return as base64."""
    Z_norm = np.clip(Z / 100.0, 0.0, 1.0)
    rgba = (_CMAP(Z_norm) * 255).astype(np.uint8)
    rgba[np.isnan(Z), 3] = 0
    img = Image.fromarray(np.flipud(rgba), 'RGBA')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def compute_contours(samples: list[dict]) -> dict:
    """
    samples: [{"lat": float, "lng": float, "scores": {"CropA": float, ...}}]
    Returns: {"CropA": {"image": "<base64 PNG>", "coordinates": [[lng,lat] x4]}}
    """
    crops = {crop for s in samples for crop in s.get("scores", {})}
    result = {}

    for crop in crops:
        pts = [(s["lng"], s["lat"], s["scores"][crop])
               for s in samples if crop in s.get("scores", {})]
        if len(pts) < 3:
            continue

        lngs, lats, scores = map(np.array, zip(*pts))
        xi, yi, Z = _interpolate(lngs, lats, scores)

        result[crop] = {
            "image": _to_raster(Z),
            "coordinates": [
                [float(xi[0]),  float(yi[-1])],
                [float(xi[-1]), float(yi[-1])],
                [float(xi[-1]), float(yi[0])],
                [float(xi[0]),  float(yi[0])],
            ],
        }

    return result
