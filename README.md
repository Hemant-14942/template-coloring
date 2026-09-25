# Template Coloring

Pick a color, preview every slide live, and download the `red-final` PowerPoint template recolored.

- **Frontend:** React 18 + Vite + TypeScript, color picker from [react-colorful](https://github.com/omgovich/react-colorful)
- **Backend:** FastAPI, recolors the `.pptx` by rewriting its slide XML (no quality loss, no re-rendering)

## Folder structure

```
template-coloring/
├── backend/
│   ├── app/
│   │   ├── main.py                  # app factory, CORS, gzip, error handlers
│   │   ├── core/                    # settings (.env), logging, exceptions
│   │   ├── api/v1/routes/           # health.py, templates.py
│   │   ├── schemas/template.py      # pydantic models + hex validation
│   │   └── services/
│   │       ├── color.py             # dark / main / bright shade maths
│   │       ├── recolor.py           # rewrites colors inside the .pptx
│   │       └── template_store.py    # loads templates from assets/
│   ├── assets/templates/red-final/
│   │   ├── template.json            # which slides change + base colors
│   │   ├── template.pptx            # the default template
│   │   ├── previews/slide-NN.jpg    # slide renders for the live preview
│   │   └── masks/slide-NN.png       # white = recolorable pixels
│   ├── scripts/generate_previews.py # rebuild previews/masks (LibreOffice)
│   ├── tests/
│   ├── requirements.txt / requirements-dev.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/                     # fetch client + template endpoints
│   │   ├── components/
│   │   │   ├── ColorPanel/          # react-colorful picker, hex input, presets, download
│   │   │   ├── SlideGrid/
│   │   │   └── SlidePreview/        # canvas recolor using the mask
│   │   ├── hooks/                   # useTemplate, useDownload, useDebouncedValue
│   │   ├── lib/color.ts             # same shade maths as the backend
│   │   ├── types/
│   │   └── styles/
│   ├── nginx.conf                   # production: serves SPA, proxies /api
│   └── Dockerfile
└── docker-compose.yml
```

## Run locally (development)

**Backend** (Python 3.11+):

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

**Frontend** (Node 18+), in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Vite proxies `/api` to the backend, so no CORS setup is needed in dev.

**Tests:**

```bash
cd backend && pytest
```

## Run in production (Docker)

```bash
docker compose up --build -d
```

Open http://localhost:8080. Nginx serves the built React app and forwards `/api` to FastAPI (gunicorn + uvicorn workers). Swagger docs are turned off when `ENVIRONMENT=production`.

## API

| Method | Path | What it does |
|---|---|---|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/templates` | List templates |
| GET | `/api/v1/templates/{id}` | Slides, what changes on each, preview and mask URLs |
| GET | `/api/v1/templates/{id}/slides/{n}/preview` | Slide render (JPEG) |
| GET | `/api/v1/templates/{id}/slides/{n}/mask` | Recolor mask (PNG) |
| POST | `/api/v1/templates/{id}/recolor` | Body `{"color": "#1F4E9A"}` → returns the `.pptx` |

## How the recoloring works

The template uses three reds: `8E0000` (dark, gradient start), `C00000` (main), `FF0000` (bright, gradient end and outlines). From the one picked color, `color.py` makes a dark and bright shade with the same ratios, so picking `#C00000` gives back the original file exactly. `recolor.py` swaps those three hex codes on every slide marked `"recolor": true` in `template.json`, and sets the theme's Accent 1 to the picked color so new shapes match too.

**To stop a slide from changing,** set `"recolor": false` for it in `template.json` and restart the backend. The preview respects this too.

## Adding another template

1. Create `backend/assets/templates/<new-id>/` with `template.pptx` and a `template.json` (copy the red-final one and edit the slides and `base_colors`).
2. Install LibreOffice and poppler, then run `python scripts/generate_previews.py assets/templates/<new-id>`.
3. Point `TEMPLATE_ID` in `frontend/src/App.tsx` to the new id (or add a template dropdown using `GET /api/v1/templates`).
