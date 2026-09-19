# ReviewLens — Data Sources

## Amazon Reviews

### Why we don't scrape Amazon live

Amazon's anti-scraping infrastructure makes direct scraping effectively
impossible through conventional methods as of 2025-26:

- **Bot fingerprinting** — headless browsers (Selenium, Playwright) are
  detected via browser API checks that real Chrome passes but headless Chrome
  fails. There is no reliable workaround at the library level.

- **Dynamic content** — product review pages load their content via internal
  XHR/fetch calls after the initial page load. BeautifulSoup on the raw HTML
  response returns an empty reviews section, regardless of how the request
  is made.

- **IP reputation** — home IPs, college network IPs, and all major cloud
  provider IP ranges (AWS, GCP, Azure, Render) are flagged near-instantly.
  Residential proxy pools are also largely flagged.

- **Silent failures** — Amazon sometimes returns HTTP 200 with a stripped page
  containing no reviews, making it impossible to distinguish a successful
  scrape from a blocked one without inspecting the response body every time.

Paid scraping APIs (ScraperAPI, Oxylabs, Bright Data) have 40–60% success
rates on Amazon specifically, making them unreliable for a demo environment
where a failed scrape during a presentation is unacceptable.

This is not a tooling or skill issue. It is a deliberate infrastructure
decision by Amazon that even well-funded engineering teams work around by
using datasets rather than live scraping.

---

### Dataset used

**McAuley Lab — Amazon Review Data (2018)**
Compiled by Jianmo Ni, Jiacheng Li, Julian McAuley (UCSD).
Published at EMNLP 2019.

| Property | Value |
|---|---|
| Category | Cell Phones & Accessories |
| Subset | 5-core (every user and product has ≥5 reviews) |
| Reviews | 1,128,437 |
| Products | ~27,000 unique ASINs |
| Period | May 1996 – Oct 2018 |
| Format | Gzipped JSON-lines (.json.gz), one review per line |
| Size | ~300 MB compressed |

**Download:**
```
https://jmcauley.ucsd.edu/data/amazon_v2/categoryFilesSmall/Cell_Phones_and_Accessories_5.json.gz
```
No account required. Direct download.

**Citation:**
> Justifying recommendations using distantly-labeled reviews and fine-grained aspects.
> Jianmo Ni, Jiacheng Li, Julian McAuley.
> EMNLP 2019.

---

### Column mapping

| McAuley column | ReviewLens schema | Notes |
|---|---|---|
| `asin` | `products.url` | Used as unique product identifier |
| `reviewText` | `reviews.review_text` | Cleaned via `scraper/cleaner.py` |
| `overall` | `reviews.rating` | Float, 1.0–5.0 |
| `reviewerName` | `reviews.reviewer_name` | Truncated to 200 chars |
| `reviewTime` | `reviews.review_date` | Parsed from "MM DD, YYYY" |
| `verified` | `reviews.verified_purchase` | Bool |
| `summary` | Fallback text | Used if `reviewText` is empty |
| `vote` | Not stored | Helpfulness votes, not needed |
| `style` | Not stored | Product variant metadata |

---

### Loading the dataset

Place the downloaded file in `data/`:
```
data/Cell_Phones_and_Accessories_5.json.gz
```

For development / demo (50,000 reviews, ~2 min):
```bash
python -m scraper.dataset_loader --file data/Cell_Phones_and_Accessories_5.json.gz --limit 50000
```

For full training data (1.1M reviews, ~20 min):
```bash
python -m scraper.dataset_loader --file data/Cell_Phones_and_Accessories_5.json.gz
```

`data/` is in `.gitignore` — the file is never committed to the repository.

---

## Flipkart Reviews

Flipkart is retained as a live scraping source because:

- Review pages are **server-rendered HTML** — BeautifulSoup on the raw
  response actually works
- Bot detection is significantly less aggressive than Amazon
- Provides a live data source for the demo (product URL → real-time analysis)

See `scraper/flipkart.py` for implementation.

**Approach:**
- Target the reviews section at `https://www.flipkart.com/product/p/reviews`
- Reviews are inside `div[class*="col EPCmJX"]` containers (verify in
  browser inspector — Flipkart class names are generated but stable within
  a version)
- Use `time.sleep(2)` between pages
- 5 pages × ~10 reviews per page = ~50 reviews per product, sufficient for demo

---

## Summary

| Source | Method | Reviews | Use case |
|---|---|---|---|
| McAuley 2018 dataset | Offline load from .json.gz | 1.1M | ML training, demo data |
| Flipkart live | requests + BeautifulSoup | ~50/product | Live demo, real-time analysis |
| Amazon live | ❌ Not feasible | — | Abandoned |
