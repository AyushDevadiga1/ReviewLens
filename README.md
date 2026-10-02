# ReviewLens

Production-level Aspect-Based Sentiment Analysis for E-Commerce Reviews.
Mumbai University C-Scheme | Natural Language Processing Mini-Project
B.E. Computer Science (AI & ML)

## What It Does

Ingests e-commerce product review datasets, filters fake ones with a trained
classifier, runs Aspect-Based Sentiment Analysis on genuine reviews, stores
everything in PostgreSQL, and serves results through a FastAPI REST API with a
Streamlit comparison dashboard.

Three-stage pipeline:

1. Fake Review Filter — DistilBERT / Logistic Regression classifier
2. ABSA — PyABSA with BERT, extracts per-aspect sentiment scores
3. Comparative Dashboard — side-by-side aspect comparison across products

## Status

Work is in progress. The target architecture below is the design; this section
is what actually runs today.

| Module | State |
|---|---|
| `db/models.py` | **Done** — 5 tables: products, reviews, fake_scores, aspect_sentiments, api_logs |
| `db/session.py` | **Done** — engine, session factory, `get_db()` FastAPI dependency, `create_tables()` |
| `data_ingestion/cleaner.py` | **Done** — `clean_review_text()`, `extract_review_metadata()` |
| `api/schemas/` | **Done** — Pydantic request/response models |
| `ml/absa/aspects.py` | **Done** — 7 canonical aspect definitions |
| `eda/` | **Done** — executed notebooks with findings baked in |
| `data_ingestion/loaders/` | Stubbed — both loaders still `pass` |
| `ml/fake_review/`, `ml/absa/inference.py` | Stubbed — training and inference not written |
| `api/services/`, `api/routers/` | Stubbed — service layer and endpoints not wired |
| `frontend/` | Stubbed — Streamlit pages not connected |
| `db/migrations/` | Skeleton only — Alembic versions directory is empty |

**21 of 99 functions have a real body.** The rest are docstring-only stubs
carrying `TODO` markers.

### Tests

```
46 test functions
├─ 13 real assertions   → all pass  (tests/test_cleaner.py)
└─ 33 docstring-only bodies
   ├─ 21 pass vacuously  (test_ingestion, test_absa, test_fake_detector)
   └─ 12 fail to collect  (test_api, test_scraper — see Known Issues)
```

Plain `pytest` runs **zero** tests: the two collection errors abort the whole
run. You need `pytest --continue-on-collection-errors` to see the
`34 passed, 2 errors` underneath it.

Only `tests/test_cleaner.py` asserts anything today. A green run mostly
measures that the placeholders are syntactically valid.

## Getting Started

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

copy .env.example .env         # Windows; cp on Linux/macOS
```

`db/session.py` calls `load_dotenv()` at import, so `.env` is picked up
automatically for local runs. Inside Docker, `docker-compose.yml` sets
`DATABASE_URL` explicitly and takes precedence.

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql://reviewlens:password@localhost:5432/reviewlens` | Postgres connection |
| `SQL_ECHO` | `False` | Log every SQL statement **and bound parameters** — review text ends up in logs. Dev only. |

Run the API once the routers are implemented:

```bash
uvicorn api.main:app --reload --port 8000
```

Full stack:

```bash
docker-compose up api db mlflow
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

**PyABSA breaks collection, which breaks the whole test run.** `metric_visualizer`
fails at import with `UpdateChecker.check() takes 1 positional argument but 3
were given`. That stops `tests/test_api.py` collecting — and because pytest
aborts on collection errors by default, a bare `pytest` runs **zero** tests
right now. It would also stop `uvicorn` starting. `pip install --upgrade PyABSA`
is the likely fix. Until then: `pytest --continue-on-collection-errors`.

**`tests/test_scraper.py` imports a module that does not exist.** Line 8 does
`from scraper.cleaner import ...`; the package is `data_ingestion` now. The
file is superseded by `tests/test_ingestion.py` and should be deleted — it is
the second collection error.

**Docstring drift in `data_ingestion/cleaner.py`.** Two comments describe the
`??????` garbling as something the non-ASCII guard handles. It cannot — `?` is
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
