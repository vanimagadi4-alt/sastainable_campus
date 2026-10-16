# EcoNova AI — Intelligent Digital Twin for Sustainable Campuses

An independently built Flask and vanilla JavaScript dashboard prototype for DSU, Harohalli. **All dashboard measurements, alerts, scores, and map statuses are demonstration data.** No campus meters or official geographic map are connected.

## Windows PowerShell setup

From this folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000>. If PowerShell blocks activation for the current terminal, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate again.

The dashboard imports the workspace `database/database.py` helper and uses its SQLite file at `../database/ecotwin.db`. On first startup, the helper creates the schema and inserts its labelled demo records. Energy, water, waste, alerts, and CSV report values are read from that database; alert status changes write back to it. The existing `database.py` source file is not modified.

If port 5000 is already in use, start the dashboard on another port:

```powershell
$env:PORT = "5001"
python app.py
```

Then open <http://127.0.0.1:5001>.

## Optional image detection

The upload API validates images even when inference dependencies are absent. It never invents detections. To enable object detection, install a PyTorch build suitable for your Windows/Python environment by following the official PyTorch selector, then run:

```powershell
pip install ultralytics
$env:YOLO_MODEL = "C:\path\to\your\model.pt"
python app.py
```

Ultralytics may download a general COCO model when configured with a recognized model name and network access. Set `YOLO_MODEL` to a local weights file to avoid ambiguity. General object detection does not establish whether an item is recyclable or hazardous; people must verify those classifications. The app does not bundle or use the original project's weights.

## Optional Ollama recommendations

Install Ollama separately, pull a model (for example `ollama pull deepseek-r1:latest`), and ensure Ollama is running. Then configure the Flask process:

```powershell
$env:OLLAMA_MODEL = "deepseek-r1:latest"
$env:OLLAMA_URL = "http://127.0.0.1:11434"
python app.py
```

If Ollama or the configured model is unavailable, the recommendations endpoint returns clearly labelled general demo guidance.

## Features

- Responsive overview with KPIs, resource charts, sustainability score, alerts, and guidance.
- Clickable illustrative SVG campus map with facility details and Energy, Water, Waste, and Alerts filters.
- Drag-and-drop and file-picker image upload with preview, size/type validation, helpful API errors, and optional YOLO detections.
- Energy and water analytics with explicit demo labels and integration limitations.
- Alert filters and persistent status changes in a local SQLite database.
- Optional local Ollama recommendations and a downloadable CSV demo report.
- JSON APIs: `/api/health`, `/api/analyze-waste`, `/api/energy`, `/api/water`, `/api/alerts`, `/api/ai-recommendations`; alert update via `PATCH /api/alerts/<id>`.

Chart.js and web fonts are loaded from CDNs, so charts and remote typography need internet access. The rest of the dashboard is served locally by Flask. If Chart.js is unreachable, the app remains navigable but chart canvases will be empty.

## Troubleshooting

- **`py` not found:** install Python 3.10+ and enable the Python launcher, then reopen PowerShell.
- **Port 5000 is busy:** set `$env:PORT = "5001"`, start the app again, and browse to `http://127.0.0.1:5001`.
- **Upload says detection unavailable:** install the optional dependencies, set `YOLO_MODEL` to an existing weights file, and restart Flask. Inference can require substantial disk space and compatible PyTorch.
- **Ollama demo guidance appears:** start Ollama, confirm the model is present with `ollama list`, set `OLLAMA_MODEL`, then restart Flask.
- **No chart appears:** check internet access for the Chart.js CDN or serve a local Chart.js copy yourself.
- **Changes to alerts persist locally:** delete `econova.db` only if you intentionally want to reset the demo alert state; the database is created on next start.

## Scope and safety

The campus map is an illustrative layout, not geographically accurate. Energy and water numbers are samples, not real sensor readings. Water flags request review and do not claim physical leak detection. Reports are labelled demo data. Uploaded images are held only temporarily during inference and removed afterward; they are not exposed through a public upload route.
