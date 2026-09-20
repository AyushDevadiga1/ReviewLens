# ReviewLens — Data Sources

Live scraping of Amazon and Flipkart was evaluated and abandoned due to dynamic
content loading, bot fingerprinting, and IP blocking — the same constraints that
cause industry teams to rely on licensed data feeds and research datasets.
ReviewLens uses two offline datasets instead.

---

## Dataset 1 — Amazon (McAuley Lab)

**McAuley Lab — Amazon Review Data (2018)**
Compiled by Jianmo Ni, Jiacheng Li, Julian McAuley (UCSD). Published at EMNLP 2019.

| Property | Value |
|---|---|
| Category | Cell Phones & Accessories |
| Subset | 5-core (every user and product has ≥ 5 reviews) |
| Reviews | 1,128,437 |
| Unique products | ~27,000 ASINs |
| Period | May 1996 – Oct 2018 |
| Format | Gzipped JSON-lines (.json.gz) — one review per line |
| Compressed size | ~300 MB |

**Download (no account required):**
```
https://jmcauley.ucsd.edu/data/amazon_v2/categoryFilesSmall/Cell_Phones_and_Accessories_5.json.gz
```
Place the file at: `data/Cell_Phones_and_Accessories_5.json.gz`

**Citation:**
> Justifying recommendations using distantly-labeled reviews and fine-grained aspects.
> Jianmo Ni, Jiacheng Li, Julian McAuley. EMNLP 2019.

### Column mapping

| McAuley column | ReviewLens schema | Notes |
|---|---|---|
| `asin` | product identifier | Groups reviews under one Product row |
| `reviewText` | `reviews.review_text` | Cleaned via `cleaner.py` |
| `overall` | `reviews.rating` | Float 1.0–5.0 |
| `reviewerName` | `reviews.reviewer_name` | Truncated to 200 chars |
| `reviewTime` | `reviews.review_date` | Parsed from "MM DD, YYYY" |
| `verified` | `reviews.verified_purchase` | Bool |
| `summary` | Fallback text | Used when `reviewText` is absent |
| `vote` | Not stored | Helpfulness votes — not needed |

### Load commands

```bash
# Dev / demo — 50k reviews (~2 min):
python -m data_ingestion.loaders.amazon_loader \
  --file data/Cell_Phones_and_Accessories_5.json.gz \
  --limit 50000

# Full training data — 1.1M reviews (~20 min):
python -m data_ingestion.loaders.amazon_loader \
  --file data/Cell_Phones_and_Accessories_5.json.gz
```

---

## Dataset 2 — Flipkart (Kaggle)

**Flipkart Products Review Dataset — 363K reviews**

| Property | Value |
|---|---|
| Reviews | ~363,000 |
| Format | CSV |
| Kaggle URL | https://www.kaggle.com/datasets/niraliivaghani/flipkart-dataset |

**Download:**
Log in to Kaggle → download → place file at: `data/flipkart_reviews.csv`

### Column mapping

| Flipkart column | ReviewLens schema | Notes |
|---|---|---|
| `Product Name` | `products.name` + product identifier | Groups reviews under one Product row |
| `Review` | `reviews.review_text` | Cleaned via `cleaner.py` |
| `Rate` | `reviews.rating` | Cast to float 1.0–5.0 |
| `Summary` | Fallback text | Used when `Review` is empty |
| *(absent)* | `reviews.review_date` = None | No date column in this dataset |
| *(absent)* | `reviews.verified_purchase` = False | No verified column |

### Load commands

```bash
# Dev / demo — 30k reviews:
python -m data_ingestion.loaders.flipkart_loader \
  --file data/flipkart_reviews.csv \
  --limit 30000

# Full dataset — ~363k reviews:
python -m data_ingestion.loaders.flipkart_loader \
  --file data/flipkart_reviews.csv
```

---

## Why scraping was abandoned

### Amazon
- Dynamic content — reviews load via internal XHR after page load; BeautifulSoup on the raw HTML returns nothing
- Bot fingerprinting — headless browsers detected via browser API checks real Chrome passes but headless Chrome fails
- IP reputation — home, college, and all cloud provider IP ranges flagged near-instantly
- Silent failures — HTTP 200 with no reviews, indistinguishable from a successful scrape without inspecting every response

### Flipkart
- Reviews per product are sparse compared to Amazon (10–30 per page vs 100+)
- Pagination causes blocking after 2–3 pages
- Getting meaningful volume (10k+ reviews) would require traversing thousands of product pages — enough traffic to trigger a ban

Paid scraping APIs (ScraperAPI, Oxylabs) have 40–60% success rates on Amazon
and are overkill for a demo. The offline dataset approach is what NLP research
teams use for the same reason.

---

## Summary

| Source | Loader | Reviews | Platform |
|---|---|---|---|
| McAuley 2018 (.json.gz) | `amazon_loader.py` | 1,128,437 | amazon |
| Flipkart Kaggle (.csv) | `flipkart_loader.py` | ~363,000 | flipkart |
| Live scraping | ❌ Abandoned | — | — |

`data/` is in `.gitignore` — dataset files are never committed.
