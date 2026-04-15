import numpy as np
from fastapi.testclient import TestClient

from backend.main import app


def test_analyze_farm_returns_fallback_when_llm_unavailable(monkeypatch):
    monkeypatch.setattr("backend.farm_analysis._fetch_weather", lambda lat, lng: "Clear, 20C")
    monkeypatch.setattr("backend.farm_analysis._fetch_forecast_summary", lambda lat, lng: "Dry week ahead")
    monkeypatch.setattr("backend.farm_analysis._fetch_elevation", lambda lat_grid, lng_grid: np.zeros((15, 15)))
    monkeypatch.setattr("backend.farm_analysis._call_claude", lambda *args, **kwargs: (_ for _ in ()).throw(TimeoutError("timeout")))

    payload = {
        "farm": {"lat": 41.8781, "lng": -93.0977, "farmSize": 250},
        "samples": [
            {
                "id": "1",
                "lat": 41.8781,
                "lng": -93.0977,
                "result": {
                    "soil": {"label": "Loam", "confidence": {"Loam": 0.9, "Clay": 0.1}},
                    "moisture": {"label": "Moist", "confidence": {"Moist": 0.8, "Dry": 0.2}},
                    "recommendations": {
                        "mode": "targeted",
                        "summary": "Good for soybeans.",
                        "tip": "Monitor moisture.",
                        "crop_analysis": [
                            {"crop": "corn", "suitable": True, "score": 72, "reason": "Balanced soil"},
                            {"crop": "soybean", "suitable": True, "score": 78, "reason": "Favorable moisture"},
                        ],
                    },
                },
            },
            {
                "id": "2",
                "lat": 41.8791,
                "lng": -93.0987,
                "result": {
                    "soil": {"label": "Clay", "confidence": {"Clay": 0.7, "Loam": 0.3}},
                    "moisture": {"label": "Wet", "confidence": {"Wet": 0.9, "Moist": 0.1}},
                    "recommendations": {
                        "mode": "targeted",
                        "summary": "Mixed result.",
                        "tip": "Improve drainage.",
                        "crop_analysis": [
                            {"crop": "corn", "suitable": False, "score": 38, "reason": "Too wet"},
                            {"crop": "soybean", "suitable": True, "score": 61, "reason": "Can tolerate wetter soil"},
                        ],
                    },
                },
            },
            {
                "id": "3",
                "lat": 41.8771,
                "lng": -93.0967,
                "result": {
                    "label": "average",
                    "confidence": {"bad": 0.2, "average": 0.6, "good": 0.2},
                },
            },
        ],
        "crops": ["corn", "soybean"],
        "satellite_b64": None,
        "bounds": {"west": -93.11, "south": 41.87, "east": -93.09, "north": 41.89},
    }

    client = TestClient(app)
    response = client.post("/analyze-farm", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "corn" in data
    assert "soybean" in data
    assert "__timeline__" in data
    assert len(data["corn"]["scores"]) == 15
    assert len(data["corn"]["scores"][0]) == 15
    assert data["corn"]["summary"]
    assert data["__timeline__"]["phases"]
