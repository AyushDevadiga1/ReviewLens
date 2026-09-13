# ReviewLens

Production-level Aspect-Based Sentiment Analysis for E-Commerce Reviews.
Mumbai University C-Scheme | Natural Language Processing Mini-Project
B.E. Computer Science (AI & ML)

## What It Does

Scrapes e-commerce product reviews, filters fake ones with a trained classifier,
runs Aspect-Based Sentiment Analysis on genuine reviews, stores everything in
PostgreSQL, and serves results through a FastAPI REST API with a Streamlit
comparison dashboard.

Three-stage pipeline:

1. Fake Review Filter — DistilBERT / Logistic Regression classifier
2. ABSA — PyABSA with BERT, extracts per-aspect sentiment scores
3. Comparative Dashboard — side-by-side aspect comparison across products

## How It Will Work

The project is a three-stage pipeline exposed through a REST API. When a user
submits a product URL, the following happens end to end:

```
product URL / review text
          │
          ▼
┌─────────────────────────┐   requests + BeautifulSoup, delays between pages,
│ 1. scraper/             │   HTML removed, unicode (NFC) normalised,
│    amazon / flipkart    │   whitespace collapsed → structured review dicts
└─────────────────────────┘
          │
          ▼
┌─────────────────────────┐   trained classifier (TF-IDF + LogisticRegression,
│ 2. ml/fake_review       │   DistilBERT optional) labels each review
│    → fake filter        │   genuine/fake with a confidence score.
└─────────────────────────┘   Fake reviews are dropped before analysis.
          │  genuine only
          ▼
┌─────────────────────────┐   PyABSA (BERT) extracts per-mention
│ 3. ml/absa              │   aspect + sentiment (positive/negative/neutral)
│    → ABSA               │   with confidence. Raw terms map to the 7
└─────────────────────────┘   canonical aspects in ml/absa/aspects.py.
          │
          ▼
┌─────────────────────────┐   products, reviews, fake_scores,
│ 4. db/                  │   aspect_sentiments and api_logs are
│    SQLAlchemy + Postgres│   persisted via the ORM models.
└─────────────────────────┘
          │
          ▼
┌─────────────────────────┐   per-aspect scores (0-10), positive/negative/
│ 5. api/services         │   neutral percentages, per-aspect winner across
│    aggregator           │   products, and weekly sentiment trends.
└─────────────────────────┘
          │
          ▼
┌─────────────────────────┐
│ 6. api/ (FastAPI)       │  serves results over HTTP with
│    /analyze /compare    │  Pydantic validation, API-key auth,
│    /trends /health      │  and rate limiting.
└─────────────────────────┘
          │
          ▼
┌─────────────────────────┐
│ 7. frontend/            │  Streamlit dashboard renders radar charts,
│    (Streamlit)          │  comparison tables and trend lines from the API.
└─────────────────────────┘
```

In short: the workflow is **scrape → clean → filter fakes → analyze aspects →
aggregate → store → serve → visualise**, in that order. Only genuine reviews
reach ABSA, so the sentiment scores reflect real customers rather than paid
reviews.

## Estimation of Effort

The build follows the reference implementation order (`docs/reviewlens_skeleton.md`) —
backend first, frontend last:

| Phase                          | Scope                                            |
|--------------------------------|--------------------------------------------------|
| Data foundation                | `db/` models + session, cleaner, Amazon scraper  |
| ML models                      | fake-review training, aspects config, ABSA       |
| Services                       | fake detector service, aggregator                |
| API                            | schemas, `/analyze` `/compare` `/trends` `/health`, app wiring |
| Frontend                       | single-product, compare, trends pages            |
| Tests                          | pytest per module, then manual Swagger check     |

The core rule: do not build the frontend until `POST /analyze` returns correct
JSON in Swagger UI.

## Modules

| Module       | Responsibility                                                    |
|--------------|-------------------------------------------------------------------|
| `api/`       | FastAPI app: routers, Pydantic schemas, ML services, middleware   |
| `db/`        | SQLAlchemy ORM models and session management                      |
| `ml/`        | Fake-review classifier training, ABSA inference, MLflow tracking  |
| `scraper/`   | Amazon India + Flipkart review scrapers and text cleaning         |
| `frontend/`  | Streamlit dashboard (single, compare, trends pages)               |
| `tests/`     | pytest unit/integration tests per module                          |
| `docs/`      | Project planning and skeleton reference documents                 |

## Repository Structure

```
reviewlens/
├── api/
│   ├── main.py
│   ├── routers/          # analyze, compare, trends, health
│   ├── schemas/          # request, response
│   ├── services/         # fake_detector, absa, aggregator
│   └── middleware/       # auth, rate_limit
├── ml/
│   ├── fake_review/      # train, evaluate, model/
│   ├── absa/             # inference, aspects
│   └── mlflow_tracking.py
├── scraper/              # amazon, flipkart, cleaner
├── db/                   # models, session, migrations/
├── frontend/             # app, pages/
├── tests/                # test_api, test_fake_detector, test_absa, test_scraper
├── docs/                 # project plan and skeleton reference
├── requirements.txt
├── .env.example
└── README.md
```