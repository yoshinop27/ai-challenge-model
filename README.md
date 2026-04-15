# SoilSense

SoilSense is a farm mapping app that lets a user:

- create a farm by acreage and location
- add soil sample points on a map
- upload either a soil image or tabular CSV data for each sample
- classify soil and moisture conditions
- generate whole-farm crop suitability analysis
- view a generated farm timeline

The frontend is a React/Vite app in `frontend/`. The backend is a FastAPI app in `backend/`.

## What You Need

- Node.js 18+
- Python 3.11+
- the model weight files in `backend/`
- a Mapbox token for the map UI

Optional but recommended for richer analysis:

- `OPENWEATHER_API_KEY`
- `OPENROUTER_API_KEY`

The app still returns fallback farm analysis when external analysis services are unavailable, but results will be less detailed.

## Environment Variables

Create a `.env` file at the repo root if you want local backend env loading.

Example:

```env
VITE_MAPBOX_TOKEN=your_mapbox_token
OPENWEATHER_API_KEY=your_openweather_key
OPENROUTER_API_KEY=your_openrouter_key
CORS_ORIGINS=http://localhost:5173
```

Frontend-only variable:

- `VITE_MAPBOX_TOKEN`: required for map rendering
- `VITE_API_BASE_URL`: optional if frontend and backend are on different origins

Backend variables:

- `OPENWEATHER_API_KEY`: optional weather enrichment for farm analysis
- `OPENROUTER_API_KEY`: optional LLM-based crop and timeline enrichment
- `OPENROUTER_TIMEOUT_SEC`: optional override for analysis timeout
- `CORS_ORIGINS`: comma-separated list of allowed frontend origins for deployed environments

## Local Setup

### 1. Install frontend dependencies

```bash
cd frontend
npm install
```

### 2. Install backend dependencies

Use your preferred virtual environment, then install:

```bash
pip install -r requirements.txt
```

### 3. Start the backend

From the repo root:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Start the frontend

In a second terminal:

```bash
cd frontend
npm run dev
```

By default the frontend runs on `http://localhost:5173`.

If your backend is running somewhere other than the same origin, set:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## How To Use The App

### 1. Open the app

Start the frontend and visit the local Vite URL, usually `http://localhost:5173`.

### 2. Enter the farm

Click through the landing page, then enter:

- farm size in acres
- latitude
- longitude
- one or more crops of interest

Select `View My Farm`.

### 3. Add soil samples

On the map:

- click inside the farm area
- choose upload type
- upload either:
  - a soil image, or
  - a CSV file
- click `Analyze`

Each uploaded sample is pinned onto the map.

### 4. Analyze the farm

After at least 3 samples are added, click `Analyze Farm`.

The app will:

- gather current farm bounds
- optionally fetch satellite imagery for the selected area
- send the farm, crops, and sample data to `/analyze-farm`
- render crop suitability overlays on the map
- generate a farm timeline when available

### 5. Review the result

You can:

- toggle crop layers
- click map locations to inspect suitability
- click `Farm Timeline` to view the generated plan
- click `Change Farm` to reset and start over

## CSV Upload Notes

CSV uploads are treated as tabular soil inputs for quality classification.

The backend expects:

- a header row
- at least one data row

If the CSV is empty or malformed, the backend returns a validation error.

## API Endpoints

The backend exposes:

- `GET /health`
- `POST /predict`
- `POST /analyze-farm`

`/predict` accepts multipart uploads.

`/analyze-farm` accepts JSON containing:

- `farm`
- `samples`
- `crops`
- optional `satellite_b64`
- optional `bounds`

## Testing

Backend:

```bash
pytest -q backend/tests
```

Frontend:

```bash
cd frontend
npm run build
```

## Deploying To Railway

This repo includes:

- `requirements.txt`
- `Procfile`
- `railway.json`

Railway start command:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

Set these Railway environment variables as needed:

- `OPENWEATHER_API_KEY`
- `OPENROUTER_API_KEY`
- `CORS_ORIGINS`

If the frontend is deployed separately, also set:

- `VITE_API_BASE_URL=https://your-backend-domain`

## Troubleshooting

### Analyze Farm hangs or fails

Check:

- the backend is running
- the frontend is pointing to the correct API origin
- `CORS_ORIGINS` includes the deployed frontend origin

### Maps do not load

Check:

- `VITE_MAPBOX_TOKEN` is set correctly

### LLM or weather features are missing

Check:

- `OPENROUTER_API_KEY`
- `OPENWEATHER_API_KEY`

The app can still return fallback analysis without them.
