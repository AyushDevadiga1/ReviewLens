# ReviewLens

Production-level Aspect-Based Sentiment Analysis for E-Commerce Reviews.
Mumbai University C-Scheme | Natural Language Processing Mini-Project
B.E. Computer Science (AI & ML)

## What It Does

Ingests e-commerce product review datasets, filters fake ones with a trained
classifier, runs Aspect-Based Sentiment Analysis on genuine reviews, stores
everything in PostgreSQL, and serves results through a FastAPI REST API with a
Streamlit comparison dashboard.

Six-stage pipeline (plus async jobs for long runs):

1. Ingest — offline Amazon/Flipkart loaders, idempotent re-runs
2. Clean — 20-char floor, HTML/whitespace/unicode handling
3. Fake Review Filter — binary TF-IDF+LR trained on 1,600 labelled reviews
4. ABSA — PyABSA multilingual, 7 canonical aspects, version-proof parsing
5. Aggregate — 0–10 scores, winners/margins, weekly trends
6. Serve — FastAPI (auth + rate limits) and Streamlit dashboard

Long product runs go through async jobs (`POST /jobs/analyze` → poll
`GET /jobs/{id}` → cancel with `DELETE`).

## Status

Everything below runs and is verified end-to-end (41/41 tests real,
no placeholders).

| Module | State |
|---|---|
| `db/models.py` | **Done** — products, reviews, fake_scores, aspect_sentiments, api_logs, analysis_jobs |
| `db/session.py` | **Done** — engine, factory, `get_db()`, `create_tables()`, thread-safe sessions |
| `data_ingestion/` | **Done** — cleaner + both loaders, idempotent, header-tolerant Flipkart mapping |
| `ml/fake_review/` | **Done** — v1 sentiment model + v2 binary fake classifier (Ott corpus, F1 0.88), MLflow logged |
| `ml/absa/inference.py` | **Done** — AspectExtractor on 2.3.x and 2.4.x, spacy + checkpoint baked in Docker |
| `ml/mlflow_tracking.py` | **Done** — experiment logging helper |
| `api/services/` | **Done** — fake detector (v2 + fallback), aggregator, ABSA wrapper, shared pipeline |
| `api/routers/` | **Done** — analyze, compare, trends, health (+metrics), products, jobs |
| `api/middleware/` | **Done** — API-key auth + per-key rate limits, `/health` and `/metrics` open |
| `frontend/` | **Done** — native multipage dashboard (Overview, Single, Compare, Trends, Pipeline) |
| `monitoring/` | **Done** — Prometheus scrapes real `/metrics`; Grafana provisioned |
| `db/migrations/` | Skeleton only — Alembic versions directory is empty (`create_tables()` used instead) |

Known limits, stated plainly: the fake model is hotel-trained (transfers at
~80–85% to phone reviews); ABSA needs minutes of CPU per hundred reviews
(hence jobs); Prometheus has no alert rules yet.

### Tests

```
41 test functions — all real, zero placeholders:
├─ 13 cleaner behaviour      (tests/test_cleaner.py)
├─ 12 ingestion mapping      (tests/test_ingestion.py)
├─ 6 aggregation math        (tests/test_absa.py)
├─ 3 detector behaviour      (tests/test_fake_detector.py)
└─ 7 API integration         (tests/test_api.py — temp DB, boots both models)
```

Plain `pytest` runs the whole suite: `41 passed`. The API tests boot
the real ABSA model, so the suite takes a few minutes — that is the
price of integration tests that actually integrate.

## Getting Started

Prerequisites: Python 3.11. Docker Desktop is **optional** — needed only
for the production-style stack, not for development.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Copy `.env.example` to `.env` (`cp` on Linux/macOS) and set the secrets —
at minimum `POSTGRES_PASSWORD` and `API_KEY_SECRET`. `db/session.py` calls
`load_dotenv()` at import, so `.env` is picked up automatically for local
runs. Inside Docker, `docker-compose.yml` values take precedence.

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Postgres connection (no default — fails fast if unset) |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | DB container init + API URL composition |
| `API_KEY_SECRET` | Shared secret hashed for the `X-API-Key` gate |
| `MLFLOW_TRACKING_URI` | Where training runs are logged |
| `SQL_ECHO` | Log every SQL statement **and bound parameters** — review text ends up in logs. Dev only. |

### Run without Docker (recommended for development)

Two terminal windows, no containers. First boot takes ~3 minutes
(model loads), then everything is instant to restart.

Terminal 1 — API (PowerShell shown; bash exports equivalently):

```powershell
cd C:\path\to\ReviewLens
$env:DATABASE_URL = "sqlite:///demo.db"
$env:API_KEY_SECRET = "demo-key"
.\.venv\Scripts\python.exe -m uvicorn api.main:app --port 8000
```

Terminal 2 — dashboard:

```powershell
cd C:\path\to\ReviewLens
$env:PYTHONPATH = "C:\path\to\ReviewLens"
$env:API_BASE_URL = "http://localhost:8000"
$env:API_KEY = "demo-key"
.\.venv\Scripts\streamlit run frontend/Overview.py
```

Open http://localhost:8501. Your analyses land in `demo.db` (safe to delete).

### Run with Docker (production parity)

| Service | How | Port | Needs |
|---|---|---|---|
| Postgres (`db`) | `docker compose up -d db` | 5433 → 5432 | — (comes first; API waits on it) |
| FastAPI (`api`) | `docker compose up -d api` **or** uvicorn above | 8000 | `db` healthy, `API_KEY_SECRET` set |
| Streamlit (`frontend`) | `docker compose up -d frontend` **or** streamlit above | 8501 | `api` reachable |
| MLflow (`mlflow`) | `docker compose up -d mlflow` | 5000 | optional (training logs only) |
| Prometheus + Grafana | `docker compose up -d prometheus grafana` | 9090 / 3000 | optional (observability only) |

Do **not** run plain `docker compose up -d` with stale images — old
`api`/`frontend` containers steal ports 8000/8501. Either rebuild first
(`docker compose build api frontend`) or start only what you need.

First run: open the dashboard → Single Product → analyse one product
(`B0002SYC5O` / `amazon` is a good demo) → Compare and Trends light up
once aspects are stored. API auth: every route except `/health` needs
the `X-API-Key` header (the dashboard sends it automatically).

Full stack from scratch:

```bash
docker compose build api frontend
docker compose up -d
```

### Why all these services

See the tables above: only `db` + `api` + `frontend` are required, and
each has a no-Docker equivalent. The rule of thumb: develop without
Docker (instant restarts, no 6 GB images); bring the stack up for
multi-user testing, observability, and anything resembling production.

Production (no dev override with `--reload` and code mounts):

```bash
docker compose -f docker-compose.yml up -d
```

Existing databases predate the `uq_aspect_mention` constraint —
`create_tables()` never alters tables, so apply it once manually:

```sql
-- must return zero rows first:
SELECT review_id, aspect, sentiment, COUNT(*)
FROM aspect_sentiments GROUP BY 1, 2, 3 HAVING COUNT(*) > 1;
ALTER TABLE aspect_sentiments
  ADD CONSTRAINT uq_aspect_mention UNIQUE (review_id, aspect, sentiment);
```

## Data Sources

Live scraping of Amazon and Flipkart was evaluated and abandoned due to dynamic
content loading, bot fingerprinting, and IP blocking — the same constraints that
cause industry teams to rely on licensed data feeds and research datasets.

ReviewLens uses two offline datasets:

| Dataset | Source | Reviews | Use |
|---|---|---|---|
| McAuley Amazon Cell Phones 5-core | [UCSD / EMNLP 2019](https://nijianmo.github.io/amazon/) | 1,128,437 | ML training + demo |
| Dataset-SA | Product Reviews CSV (`data/Dataset-SA.csv`) | 205,052 | Second-source demo data |

`docs/data_sources.md` still documents a Flipkart/Kaggle CSV in place of
Dataset-SA. The cleaner's thresholds were derived from Dataset-SA, so that
doc needs the same update.

### What the EDA settled

Both notebooks in `eda/` are committed with their outputs. The findings that
drove `cleaner.py`:

| Finding | Consequence |
|---|---|
| Amazon review length: min 1, mean 277, max 33,457 | 20-char floor — single words carry no aspect signal |
| Amazon `reviewTime` is inconsistent: `8 4, 2014` alongside `02 12, 2014` | Three strptime formats tried in order |
| Amazon: 33,971 rows from `Amazon Customer` | Stored as-is, not treated as special |
| Dataset-SA `Summary` is the useful text; `Review` is a short title | `Summary` is primary, `Review` is fallback |
| Dataset-SA: no contradictory `Sentiment`/`Rate` pairs | Labels are trustworthy |
| Dataset-SA `product_name` carries `??????` mojibake | Handled in product names, not review text |

That last row is the subtle one. Measured over the full files:

| Field | Rows with a 3+ `?` run | Verdict |
|---|---|---|
| Amazon `reviewText` | 1,013 | Legitimate emphasis — `"ARE YOU KIDDING ME?????"` |
| Dataset-SA `Review` + `Summary` | 2 | Negligible |
| Dataset-SA `product_name` | 50,424 | Genuine mojibake |

`750 m??/hr` was originally `750 m³/hr` — one 2-byte character decoded to two
`?`. So `?` count equals undecodable **byte** count, and no run-length
threshold can tell damage from a reviewer shouting. Stripping runs from review
text would delete 1,013 legitimate emphasis marks to repair 2 rows, erasing
the anger signal ABSA depends on. A product name cannot ask a question, so
`?` stripping belongs there instead.

## Known Issues

**Fake model is hotel-trained.** The v2 classifier learned on Ott hotel
reviews; phone-review transfer runs ~80–85%, not the 88% in-domain number.
Short one-liners stay genuinely ambiguous — the model leans genuine there.

**ABSA is CPU-slow.** ~7s per review means the demo product takes ~20 min;
that is why product analysis runs as cancellable background jobs. No GPU
path is configured.

**Docstring drift in `data_ingestion/cleaner.py`.** Two comments describe the
`??????` garbling as something the non-ASCII guard handles. It cannot - `?` is
`U+003F`, inside `\x00-\x7F`. That guard fires on 0 Amazon rows and 4
Dataset-SA rows out of 1,538,541 text fields. The HTML strip is the rule doing
real work, on 7,451 Amazon rows.

**Alembic migrations are empty.** `db/migrations/versions/` has only a
`.gitkeep`, so the schema exists in `db/models.py` but has no migration
history.

**`pyproject.toml` names packages that do not exist.** `scraper` is listed under
`known-first-party`, and `data_ingestion` is missing from both `src` and
`known-first-party`.

## How It Works

```
datasets (Amazon JSON + Dataset-SA CSV)
          │
          ▼
┌─────────────────────────┐   Two loaders normalise both datasets
│ data_ingestion/         │   into the same schema via cleaner.py,
│   loaders/              │   then batch-write to PostgreSQL.
│   amazon_loader.py      │
│   flipkart_loader.py    │
└─────────────────────────┘
          │
          ▼
┌─────────────────────────┐   Trained classifier (TF-IDF + LogisticRegression,
│ ml/fake_review/         │   DistilBERT optional) labels each review
│   → fake filter         │   genuine/fake with a confidence score.
└─────────────────────────┘   Fake reviews are dropped before analysis.
          │  genuine only
          ▼
┌─────────────────────────┐   PyABSA (BERT) extracts per-mention
│ ml/absa/                │   aspect + sentiment (positive/negative/neutral)
│   → ABSA inference      │   with confidence. Raw terms map to the 7
└─────────────────────────┘   canonical aspects in ml/absa/aspects.py.
          │
          ▼
┌─────────────────────────┐   products, reviews, fake_scores,
│ db/                     │   aspect_sentiments and api_logs are
│   SQLAlchemy + Postgres │   persisted via the ORM models.
└─────────────────────────┘
          │
          ▼
┌─────────────────────────┐   Per-aspect scores (0–10), positive/negative/
│ api/services/           │   neutral percentages, per-aspect winner across
│   aggregator            │   products, and weekly sentiment trends.
└─────────────────────────┘
          │
          ▼
┌─────────────────────────┐
│ api/ (FastAPI)          │   Serves results over HTTP with Pydantic
│   /analyze /compare     │   validation, API-key auth, rate limiting.
│   /trends /health       │
└─────────────────────────┘
          │
          ▼
┌─────────────────────────┐
│ frontend/ (Streamlit)   │   Radar charts, comparison tables,
│                         │   and trend lines from the API.
└─────────────────────────┘
```

## Modules

| Module              | Responsibility                                                 |
|---------------------|----------------------------------------------------------------|
| `data_ingestion/`   | Dataset loaders (Amazon JSON, Flipkart CSV) and text cleaning  |
| `api/`              | FastAPI app: routers, Pydantic schemas, ML services, middleware |
| `db/`               | SQLAlchemy ORM models and session management                   |
| `ml/`               | Fake-review classifier training, ABSA inference, MLflow        |
| `frontend/`         | Streamlit dashboard (single, compare, trends pages)            |
| `tests/`            | pytest unit/integration tests per module                       |
| `docs/`             | Project planning, skeleton reference, data source docs         |

## Repository Structure

```
reviewlens/
├── data_ingestion/
│   ├── cleaner.py            # shared text preprocessing — implemented
│   ├── loaders/
│   │   ├── amazon_loader.py  # McAuley JSON → PostgreSQL      [stub]
│   │   └── flipkart_loader.py# second-source CSV → PostgreSQL [stub]
│   └── __init__.py
├── api/
│   ├── main.py
│   ├── routers/              # analyze, compare, trends, health   [stub]
│   ├── schemas/              # request, response                  [implemented]
│   ├── services/             # fake_detector, absa, aggregator    [stub]
│   └── middleware/           # auth, rate_limit                   [stub]
├── ml/
│   ├── fake_review/          # train, evaluate, model/            [stub]
│   ├── absa/                 # aspects [implemented], inference [stub]
│   └── mlflow_tracking.py                                      [stub]
├── db/                       # models + session [implemented], migrations/ [empty]
├── frontend/                 # app, pages/                        [stub]
├── tests/                    # test_cleaner [13 real], test_ingestion,
│                             # test_api, test_absa, test_fake_detector, test_scraper
├── eda/                      # executed notebooks, outputs retained
├── docs/                     # project plan, skeleton, data_sources.md
├── data/                     # gitignored — place dataset files here
├── requirements.txt
├── .env.example
└── README.md
```

## Implementation Order

Backend first, frontend last. Do not build the frontend until `POST /analyze`
returns correct JSON in Swagger UI.

| Phase | Scope | State |
|---|---|---|
| 1. DB foundation | `db/models.py` → `db/session.py` | ✅ done |
| 2. Data ingestion | `data_ingestion/cleaner.py` → `amazon_loader.py` → `flipkart_loader.py` | 🚧 cleaner done, loaders stub |
| 3. ML models | fake-review training → aspects config → ABSA inference | 🚧 aspects done, rest stub |
| 4. Services | fake detector service → aggregator | ⬜ not started |
| 5. API | schemas → routers → app wiring | 🚧 schemas done, routers stub |
| 6. Frontend | single-product → compare → trends | ⬜ not started |
| 7. Tests | pytest per module → manual Swagger check | 🚧 13 of 46 tests assert anything |

Phase 1 is finished. Phase 2 is the current work — `cleaner.py` is done and
covered, so `amazon_loader.py` is next.
