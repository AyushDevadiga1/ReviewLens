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

## Data Sources

Live scraping of Amazon and Flipkart was evaluated and abandoned due to dynamic
content loading, bot fingerprinting, and IP blocking — the same constraints that
cause industry teams to rely on licensed data feeds and research datasets.

ReviewLens uses two offline datasets:

| Dataset | Source | Reviews | Use |
|---|---|---|---|
| McAuley Amazon Cell Phones 5-core | [UCSD / EMNLP 2019](https://nijianmo.github.io/amazon/) | 1,128,437 | ML training + demo |
| Flipkart Products Review Dataset | [Kaggle](https://www.kaggle.com/datasets/niraliivaghani/flipkart-dataset) | 363,000 | Flipkart demo data |

See `docs/data_sources.md` for full column mappings and download instructions.

## How It Works

```
datasets (Amazon JSON + Flipkart CSV)
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
│   ├── cleaner.py            # shared text preprocessing
│   ├── loaders/
│   │   ├── amazon_loader.py  # McAuley JSON → PostgreSQL
│   │   └── flipkart_loader.py# Flipkart CSV → PostgreSQL
│   └── __init__.py
├── api/
│   ├── main.py
│   ├── routers/              # analyze, compare, trends, health
│   ├── schemas/              # request, response
│   ├── services/             # fake_detector, absa, aggregator
│   └── middleware/           # auth, rate_limit
├── ml/
│   ├── fake_review/          # train, evaluate, model/
│   ├── absa/                 # inference, aspects
│   └── mlflow_tracking.py
├── db/                       # models, session, migrations/
├── frontend/                 # app, pages/
├── tests/                    # test_api, test_fake_detector, test_absa, test_ingestion
├── docs/                     # project plan, skeleton, data_sources.md
├── data/                     # gitignored — place dataset files here
├── requirements.txt
├── .env.example
└── README.md
```

## Implementation Order

Backend first, frontend last. Do not build the frontend until `POST /analyze`
returns correct JSON in Swagger UI.

| Phase | Scope |
|---|---|
| 1. DB foundation | `db/models.py` → `db/session.py` |
| 2. Data ingestion | `data_ingestion/cleaner.py` → `amazon_loader.py` → `flipkart_loader.py` |
| 3. ML models | fake-review training → aspects config → ABSA inference |
| 4. Services | fake detector service → aggregator |
| 5. API | schemas → routers → app wiring |
| 6. Frontend | single-product → compare → trends |
| 7. Tests | pytest per module → manual Swagger check |
