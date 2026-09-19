"""
amazon.py
Amazon India review scraper — DEPRECATED (not used in production pipeline).

## Why this file is a stub

Amazon's anti-scraping infrastructure as of 2025-26 makes direct scraping
effectively impossible through conventional methods:

  - Bot fingerprinting: headless browsers (Selenium, Playwright) are detected
    via browser API checks that headless Chrome fails
  - Dynamic content: reviews are loaded via internal XHR APIs, not in the
    initial HTML response — BeautifulSoup on the raw page returns nothing
  - IP reputation: home, college, and cloud VM IPs are flagged near-instantly
  - Silent failures: Amazon sometimes serves a stripped page with no reviews
    and returns HTTP 200 — you think it worked but got nothing

Proxies and paid scraping APIs have 40-60% success rates on Amazon
specifically, making them unreliable for a demo environment.

## What we use instead

ReviewLens uses the McAuley Lab "Amazon Review Data (2018)" dataset:

  Dataset : Cell Phones & Accessories — 5-core subset
  Reviews : 1,128,437 real Amazon reviews
  Columns : reviewerID, asin, reviewerName, vote, reviewText,
            overall (rating 1-5), summary, unixReviewTime,
            reviewTime, verified, style
  Download: https://jmcauley.ucsd.edu/data/amazon_v2/categoryFilesSmall/
            Cell_Phones_and_Accessories_5.json.gz
  Format  : gzipped JSON-lines (.json.gz), one review per line
  Citation: Ni et al., EMNLP 2019 — "Justifying recommendations using
            distantly-labeled reviews and fine-grained aspects"

The dataset loader lives in: scraper/dataset_loader.py
It reads the .json.gz file and maps McAuley columns → ReviewLens schema,
then writes to PostgreSQL via the same DB session used by the live pipeline.

## If you want to attempt live scraping in the future

Flipkart is significantly more scrapeable — server-rendered HTML,
less aggressive bot detection. See scraper/flipkart.py.

ScraperAPI (https://www.scraperapi.com) has a free tier (1000 req/month)
that handles proxy rotation and JS rendering, and works on Amazon at
demo scale. Requires API key in .env as SCRAPER_API_KEY.
"""

# This file is intentionally not implemented.
# See scraper/dataset_loader.py for the actual data ingestion pipeline.
