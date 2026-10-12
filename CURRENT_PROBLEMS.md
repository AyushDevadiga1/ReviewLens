# CURRENT_PROBLEMS.md — ReviewLens Frontend Evaluation

**Date:** 2026-10-12
**Tester perspective:** first-time user with no code knowledge, just the running app at `http://localhost:8501`
**Environment:** Docker Compose stack (`api`, `db`, `frontend`, `mlflow`, `prometheus`, `grafana`) on a 4-CPU / 5 GB VM; API healthy (`/health/` → 200, 73 products / 1 504 reviews)
**Method:** every page and every interactive widget was exercised in a real browser (clicks, typing, keyboard selection) *and* cross-checked with direct `curl` calls to the API, so each problem below says whether the **frontend**, the **API**, or the **data** is at fault.

---

## 1. Executive summary

The frontend is fundamentally **working now**: all 5 pages load, every chart type renders (radar, gauge, grouped bar, stacked bar, trend line + volume bars), the background-job analysis flow completes end-to-end, and error messages from the API reach the screen. The earlier "components are not working" impression comes from a combination of **slow Streamlit reruns (10–120 s per action)**, **result panels that vanish on the next click**, and a few **genuinely flaky widgets** — not from dead code.

| Area | Verdict |
|---|---|
| Overview page | ✅ renders fully, live stats correct |
| Single Product — DB mode | ✅ works via background job; polling is manual (tedious) |
| Single Product — review mode | ✅ works; ~14 s per analysis |
| Compare Products | ⚠️ works only if **all** picked products are already analysed; results disappear on any later click; dropdown is flaky |
| Sentiment Trends | ⚠️ renders, but the "weeks" window is semantically wrong (see P-6) |
| Pipeline page | ✅ renders; its "live numbers" panel is session-coupled and usually empty |
| Sidebar / auth | ⚠️ key override silently lost on browser refresh |

---

## 2. Measured wait times (what a user actually feels)

All measured on this VM, from click to visible result. "Rerun" is Streamlit re-executing the whole page script.

| Action | Wait before result appears | Where the time goes |
|---|---|---|
| Open any page (first visit) | **4–8 s** | Streamlit script run + Plotly bundle load; Segment.io telemetry call adds delay |
| Any widget click (radio, chip, slider) | **1–4 s** | full-script rerun, no visible feedback ("RUNNING…" top bar only) |
| Single review **Analyze** | **≈14 s** (measured `real 13.7 s` via curl; UI identical) | CPU-bound ABSA in the API, synchronous request |
| DB product **Analyze** (59 reviews) | submit ≈1 s → job finishes **≈1.5–2 min** (30/59 → 50/59 → 59/59 across polls) | background job worker thread; **but progress only updates when you press "Check status"** |
| DB product **Analyze** (171-review product) | **>5–10 min** (not re-run during this test; known CPU bottleneck) | torch on 2 threads |
| Compare **Compare** button (2 analysed products) | **up to ~2 min** worst case (one clean run finished inside a 45 s window; another took 119 s wall-clock) | API answers in **0.3 s** — the delay is Streamlit rerun + rendering 2 Plotly charts |
| Trends **Show Trend** | **≈43 s** (measured) | API is fast; page rerun + chart render dominates |
| Sidebar health indicator refresh | up to **30 s** (cache TTL) | by design |

**Headline problem:** the API is fast (0.3–14 s for everything tested). Almost all perceived slowness is **Streamlit rerun + chart rendering**, so users experience 15 s–2 min waits for data the server produced in milliseconds.

---

## 3. Page-by-page findings

Severity: 🔴 broken/misleading · 🟠 major UX problem · 🟡 minor · ⚪ observation

### 3.1 Overview page (`/`)

- ✅ Hero, live-backend stats (73 products / 1 504 reviews — correct vs API), XAI explainer, benchmark bar chart (87.8 % / 88.1 %), pipeline diagram, "Start here" links — all render.
- 🟡 **External telemetry from a local app:** the browser makes repeated calls to `https://api.segment.io` (Streamlit usage stats). On an offline/slow network this delays first paint; on a client machine it is an unexpected data leak. Fix: `.streamlit/config.toml` → `[browser] gatherUsageStats = false`.
- ⚪ Console shows only benign warnings (`Unrecognized feature: 'battery'` etc.) and one iframe-sandbox warning from the third-party searchbox component. No JS errors.

### 3.2 Single Product page (`/Single_Product`)

Tested both input modes end-to-end.

**Database-product mode**
- ✅ Product searchbox (third-party `streamlit_searchbox`, react-select in an iframe) searches as you type (≥2 chars) and returns name + platform + review count.
- ✅ **Analyze** correctly disabled until a product is picked.
- ✅ After submitting, a job panel appears: **Check status** / **Cancel job**, progress bar (`running — 30/59 reviews`, 50 %…84 %…100 %), final render of: fake-rate gauge (11.9 %), "Genuine reviews 52 / 59" metric, radar chart, stacked sentiment-mix bar, and the aspect table (Aspect / Score / Label / Mentions). All numbers consistent with the API.
- 🟠 **Polling is manual.** The docstring says this avoids a blocking loop, but the user must click **Check status** repeatedly (2–4 clicks per analysis) to see progress. A `st.fragment` auto-refresh (or `st.autorefresh`-style 3 s loop while `status in {queued, running}`) would keep Cancel clickable *and* remove the babysitting.
- 🟡 Searchbox needs **2 characters minimum** with zero on-screen hint; typing 1 char shows an empty dropdown and nothing else.
- 🟡 The searchbox is an **iframe widget** — it doesn't inherit page fonts/theme perfectly, isn't reachable by screen readers in order, and selection state is invisible to Streamlit until the component round-trips (a mouse-selection attempt did not register; keyboard Enter did). Real users clicking normally are fine, but it's fragile.
- 🟡 When a job finishes, the result stays in `st.session_state["job_state"]` forever — there is no "clear results" or "new analysis" button; re-searching another product keeps showing the old result panel until you press Analyze again.
- ⚪ `_render_fake_trace` honestly labels its length rules as a "legacy cross-check", but a tester cannot see the actual model probability that decided the verdict (the API doesn't return it) — the "Why this verdict?" expander explains the *heuristic*, not the classifier.

**Single-review mode**
- ✅ Textarea + star slider + Analyze; verdict trace expander; fake gauge; radar; sentiment mix; table. A mixed review ("battery good / display dim / delivery late") correctly produced Battery 10 positive, Display 0 negative, Delivery 0 negative.
- 🟠 **Analyze stays disabled after typing until you press Ctrl+Enter or click outside the box** — Streamlit's textarea "apply" semantics. The hint "Press Ctrl+Enter to apply" only appears *while focused*, so it's easy to type, move the mouse to Analyze, and find it dead. This is exactly the kind of thing that reads as "components not working".
- 🟡 A single review is a degenerate case for every chart (1-point radar, 1-bar sentiment mix). Works, but looks broken/empty — consider suppressing charts for `total_reviews == 1` and showing only the table + verdict.

### 3.3 Compare Products page (`/Compare_Products`)

- ✅ With two already-analysed products the full flow renders: multi-series radar (8 aspects), grouped bar chart, **Scoreboard** table with 🟢/🟡/🔴 colour coding and `—` for missing aspects, a "🏆 B0002SYC5O takes 7 of 8 aspects" callout, per-aspect winner lines with margins, and a "How are winners computed?" expander.
- 🔴 **Results vanish on the next interaction.** Everything renders inside `if st.button("Compare")`, so *any* subsequent rerun — adding/removing a chip, moving the mouse into another widget, a stray click — wipes all charts and tables with no warning and no way to restore them except pressing Compare again (and waiting up to 2 min). This was reproduced three times during testing. Fix: store the response in `st.session_state["compare_result"]` and render from state.
- 🔴 **Multiselect dropdown is flaky.** The option list stays open after selecting a chip; typed-but-uncommitted text silently became a *third* selection when I clicked the Compare button, and one run then failed with "You can only select up to 3 options" even though I had chosen two. A tester who types a partial product name before clicking Compare will routinely add a phantom product.
- 🟠 **Analysed-vs-unanalysed is a data minefield.** Only 2–3 products in the DB have aspect data; picking any other pair returns `404 "Product 'B0002IBRBG' has not been analyzed yet."` The page explains this in the intro text (good), but the dropdown gives **no visual cue** which products are analysable — a user's first attempt will most likely 404. Fix: badge options (" analysed ✓") from a per-product aspect-count endpoint, or grey out unanalysed ones.
- 🟡 Wait after pressing Compare is 15 s–2 min with only a spinner ("Aggregating aspect scores…") — and the API actually takes 0.3 s. The spinner text blames the wrong component.
- ⚪ Winners list order is arbitrary (not sorted by margin); the "takes N of M aspects" callout is a nice touch.

### 3.4 Sentiment Trends page (`/Sentiment_Trends`)

- ✅ Searchbox → aspect multiselect (defaults to Battery Life) → weeks slider (1–52, default 8) → **Show Trend** renders a combo chart: score line + mention-volume bars on a secondary axis, a "Direction" metric (`declining`) with an explanatory alert, and a "How is the trend computed?" expander. All rendered in ≈43 s.
- 🔴 **"Weeks" filter means week-of-year, not "the last N weeks".** With `weeks=8` the API returned buckets `2015-W33, 2016-W18, 2016-W30, 2016-W32, 2016-W45, 2016-W48, 2026-W32, 2026-W37` — eight *arbitrary* ISO weeks spanning eleven years, plotted as adjacent points on the x-axis. The chart implies a continuous time series that does not exist, and the "declining" verdict compares 2015 to 2026. **The frontend label "Weeks of history" is therefore actively misleading.** (API-side bug in `GET /trends/` filtering; frontend inherits it.)
- 🟠 The trend line connects points across multi-year gaps as if they were consecutive weeks — visually smooth, analytically wrong. Even until the API is fixed, the chart should break the line on gaps (e.g. Plotly `connectgaps=False`) and label the real dates.
- 🟡 ~43 s for one line chart is far too long for a GET that answers instantly in curl; same Streamlit-rerun root cause.
- 🟡 Product search here has the same 2-char minimum and iframe quirks as Single Product.

### 3.5 Pipeline page (`/Pipeline`)

- ✅ Six-stage write-up renders with live DB counts (1 504 reviews / 73 products — correct).
- 🟠 **The "live numbers" panel almost never has data:** it reads `st.session_state["last_analysis"]`, which only exists if you analysed something *in this browser session, without refreshing*. After any page refresh (which I did between pages) the page shows only "Run an analysis on the Single Product page — its numbers will appear here." — even though analyses ran minutes ago and their results are stored in Postgres. A page that promises "live numbers to prove each stage runs" then shows none feels broken. Fix: fetch the latest completed job (`GET /jobs?latest=done`) or a recent `aspect_sentiments` sample from the API instead of session state.
- ⚪ The stage descriptions are accurate and genuinely good (idempotent loads, dedup keys, score formulas all match the code/API behaviour I verified).

### 3.6 Sidebar / auth (all pages)

- ✅ Pulsing health dot with product/review counts; updates within 30 s.
- ✅ API-key override box (`type=password`, show-toggle, help text "Changing the key clears cached API responses").
- 🟠 **The override is lost on browser refresh / any full page load.** It lives only in `st.session_state`; a F5 or pasted URL starts a fresh session and silently falls back to the env key. In a deployment where the env key is absent or different, every page breaks after one refresh with confusing per-widget 401 errors. Fix: persist to `st.cache_resource`/query-param, or at least show "using env key" vs "using override" in the sidebar.
- 🟡 **A wrong key gives no immediate feedback.** `/health` is intentionally unauthenticated, so the sidebar happily shows "API healthy" while every data call fails with `API 401: ...` errors scattered per widget. A single "🔑 key rejected" banner (probe any authenticated endpoint when the key changes) would prevent a lot of confusion.
- 🟡 The key box has no placeholder/example, so a first-time user doesn't know a key even exists until they read the help tooltip.

---

## 4. Cross-cutting problems

1. 🔴 **Streamlit rerun architecture is the #1 issue.** Every interaction re-runs the whole script; on this CPU-only VM that is 1–4 s for widgets and 15 s–2 min when Plotly charts render. Options, in increasing effort: render charts with `st.plotly_chart(config=...)` only once and cache figures (`@st.cache_data` on the figure builder); wrap results in `st.fragment`s so widgets don't rerun the world; move Compare/Trend computations behind the same job+poll pattern already used on Single Product.
2. 🔴 **Ephemeral results.** Compare output (and Pipeline's numbers) live in button-triggered branches or session state that dies on refresh. Any result a user worked hard to produce should survive reruns and, ideally, refreshes.
3. 🟠 **Product names are mojibake:** `Crompton 75 L Desert Air Cooler??????(White, Teal, ACGC-DAC751)` — the `??????` is mangled Unicode from the Flipkart CSV load (encoding at ingest, not a frontend bug), but it is displayed in *every* dropdown, chart legend, table header and winner line, and it's the single most visible quality signal of the whole app. Fix at the loader (read CSV as `utf-8` with fallback, or strip) and clean the stored names.
4. 🟠 **Search semantics:** `GET /products/search?query=flipkart` → 404 "No products matching 'flipkart'" even though 30+ Flipkart products exist — search matches `product_name` only. Users naturally type platform ("amazon"), category ("cooler") or brand ("oneplus"); "cooler"/"oneplus" happen to work, platform doesn't. Also, "no results" as HTTP 404 forces the frontend to swallow the reason and show an empty dropdown with no explanation.
5. 🟡 **No loading affordance on fast interactions:** widget changes give 1–4 s of frozen UI with no spinner; only the tiny "RUNNING…" bar. Buttons that trigger API calls should show `st.spinner` immediately (Compare and Trend do; the job panel's Check status does not).
6. ⚪ Rate limit is 100 req/min/key — not hit during testing, but rapid re-clicking Compare/Trend during slow reruns could trip it; no 429-specific handling exists in `api_client.py`.

---

## 5. What I could not verify (limitations)

- **Cancel job** was never exercised mid-run (the 59-review job finished before a cancel click could be tested) — the button and `DELETE /jobs/{id}` route exist; cancellation semantics are unverified.
- **171-review product end-to-end** was not re-run (>10 min on this VM); its behaviour is inferred from the 59-review job and earlier direct `/analyze` timings.
- **The 3-product Compare failure path** showed an error in the DOM but the snapshot truncated before the message text; the same 404 was confirmed via curl, so the message format `API 404: Product 'X' has not been analyzed yet.` is what users see.
- Mobile/narrow-viewport layout was not tested (desktop 1440×900 only).
- Grafana/Prometheus/MLflow UIs were out of scope (frontend-only evaluation).

---

## 6. Prioritised fix list

| # | Fix | Effort | Impact |
|---|---|---|---|
| 1 | Persist Compare result in session state; render from state, not from `if st.button` | S | removes the worst "components broken" symptom |
| 2 | Auto-refresh job panel while `status in {queued, running}` (st.fragment, 3 s) | S | removes manual polling |
| 3 | Fix `GET /trends/` weeks filter to mean "last N calendar weeks"; break line on gaps | M | makes Trends honest |
| 4 | Badge analysed products in Compare dropdown (and searchbox) | M | prevents first-run 404 frustration |
| 5 | Clean mojibake product names at ingest + migration for stored rows | S | biggest visual-quality win |
| 6 | Enable `gatherUsageStats = false`; cache built figures | S | cuts first-paint and rerun delays |
| 7 | Fix Compare multiselect phantom-selection (close dropdown on select / commit on change) | M | stops wrong product being submitted |
| 8 | Auto-apply textarea (or move Analyze-enable check to live widget value) | S | removes dead-button confusion |
| 9 | Pipeline page: fetch last completed analysis from API, not session state | S | makes the page's promise true |
| 10 | Show auth-failure banner once when the effective key is rejected | S | removes silent 401 confusion |
