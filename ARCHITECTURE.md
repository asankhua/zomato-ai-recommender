# Zomato AI Restaurant Recommendation Service — Architecture Document

## 1. Overview

This document describes the architecture for an AI-powered restaurant recommendation service inspired by Zomato. The system takes user preferences (place, rating, and optionally price and cuisine), uses a pre-loaded dataset of restaurants, processes with an LLM, and surfaces recommendations through a UI.

**Core flow:**  
**User Input → Filter Data → LLM Processing → Display Recommendations via UI**

---

## 2. High-Level Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   User Input    │────▶│ Filter & Process │────▶│ LLM Processing  │────▶│  UI (Display)   │
│  (Place, etc.)  │     │  (Pre-loaded CSV)│     │ (Recommendations)│     │ Recommendations │
└─────────────────┘     └──────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## 3. Input Specification

| Input   | Mandatory | Description / Constraints                          |
|---------|-----------|----------------------------------------------------|
| **Place**   | Yes       | Location / city / area for restaurant search       |
| **Rating**  | Yes       | Minimum rating filter (e.g. 4.0)                   |
| **Price**   | No        | Budget / price range (e.g. 1500)                  |
| **Cuisine** | No        | Preferred cuisines (one or more)                  |

All inputs are validated and normalized before use in data fetch and LLM steps.

---

## 4. Data Source

- **Dataset:** Pre-loaded CSV file (`phase4/data/cleaned.csv`) with **~1000 optimized rows**
- **Original source:** `ManikaSaini/zomato-restaurant-recommendation` (~51,717 rows)
- **Optimization:** Dataset is pre-filtered to include best coverage: **29 locations**, **63 cuisines**, top-rated restaurants
- **Usage:** CSV is loaded at application startup; no runtime API calls needed
- **Benefits:** Fast startup (<1s), minimal resource usage, GitHub-hosted (172KB)

---

## 5. Data Cleaning Rules Pipeline

A dedicated **Data Cleaning Pipeline** runs on raw dataset rows before filtering and LLM processing.

| Field    | Rule | Example |
|----------|------|--------|
| **Price**  | Convert to integer: strip commas, spaces, currency symbols; parse as int. | `"1,500"` → `1500`, `"₹2,000"` → `2000` |
| **Rating** | Extract numeric float from string; ignore suffix (e.g. `/5`). Treat `"NEW"` as `0.0` to retain unrated restaurants. | `"4.1/5"` → `4.1`, `"4.5"` → `4.5`, `"NEW"` → `0.0` |
| **Cuisines** | Parse delimited string into a list/array of trimmed strings; normalize separators (comma, pipe, etc.). | `"North Indian, Chinese"` → `["North Indian", "Chinese"]` |

- **Validation:** Drop or flag rows where required fields (e.g. place, rating) cannot be cleaned or are missing.  
- **Output:** Clean records (e.g. JSON/DataFrame) consumed by the filtering and LLM modules.

---

## 6. Phased Implementation Plan

The project is split into phases. **Do not start implementation** until the design is approved; this document is architecture-only.

---

### Phase 1: Project Setup & Data Access

**Goal:** Reproducible environment and access to pre-optimized dataset.

- **1.1** Define project structure (e.g. `src/`, `data/`, `tests/`, config).
- **1.2** Set up dependency management (e.g. `requirements.txt` / `pyproject.toml`).
- **1.3** Use pre-generated CSV (`phase4/data/cleaned.csv`) with ~1000 optimized rows.
- **1.4** Document required env vars (e.g. `GROQ_API_KEY`) and add a `.env.example`.

**Deliverables:** Project skeleton, pre-loaded dataset, dependency file, and minimal docs.

---

### Phase 2: Data Cleaning Pipeline

**Goal:** Reusable, testable cleaning logic aligned with the rules above.

- **2.1** Implement **cleaning functions** per field:
  - **Price:** string → integer (strip commas/symbols, parse).
  - **Rating:** string → float (handle `X.X/5` and plain numbers).
  - **Cuisines:** string → list of strings (split, strip, normalize).
- **2.2** Add a **pipeline orchestrator** that:
  - Takes raw rows (from Phase 1).
  - Applies cleaning rules.
  - Validates and drops invalid/incomplete rows.
  - Outputs clean records (e.g. in-memory structures or staged files).
- **2.3** Unit tests for each cleaner and the pipeline (edge cases: empty, malformed, different formats).
- **2.4** Optional: persist cleaned dataset (e.g. CSV/Parquet) for faster reruns.

**Deliverables:** Cleaning module, pipeline entrypoint, tests, and optional cleaned dataset artifact.

---

### Phase 3: Filtering & LLM Integration

**Goal:** Filter cleaned data by user inputs and use an LLM to generate natural-language recommendations.

- **3.1** **Filtering layer:**
  - Inputs: Place (mandatory), Rating (mandatory), Price (optional), Cuisine (optional).
  - Apply filters on pre-loaded data: place matches `location` or `listed_in(city)`, rating ≥ user rating, price ≤ user price if given, cuisine overlap if given.
  - Return a candidate set of restaurants (e.g. top N or all matching).
- **3.2** **LLM integration:**
  - **LLM provider: Groq** — use the Groq API for inference; `GROQ_API_KEY` in root `.env` or phase3 `.env`.
  - Define a **prompt template:** user inputs + candidate restaurants → ranked recommendations with reasoning.
  - **Fallback when GROQ_API_KEY missing or API error:** Return top N candidates sorted by rating with descriptive reasons (cuisine, price, rating context). No 500 error; app remains usable.
- **3.3** **Recommendation service:**
  - Single entrypoint: `(place, rating, price?, cuisine?) → recommendations`.
  - Internally: load cleaned data → filter → call LLM (or fallback) → return structured output.

**Deliverables:** Filtering logic, LLM client, fallback behavior, and env configuration. Dynamic rating filter based on selected location.

---

### Phase 4: Backend API

**Goal:** Expose the recommendation service over HTTP for the UI.

- **4.1** **HTTP API** (FastAPI):
  - POST (or GET) endpoint accepting: `place`, `rating`, optional `price`, optional `cuisine`.
  - Validates inputs and returns JSON: list of recommendations (name, reason, rating, cuisine, price, address) + summary + metadata.
  - GET `/locations` — returns area names only (`listed_in(city)` and `location`), *not* detailed addresses (e.g. BTM, Banashankari).
  - GET `/cuisines` — unique cuisines for dropdown.
  - Root `/` returns API info; all endpoints also available under `/api/*` for client flexibility.
- **4.2** CORS enabled for UI; loads root `.env` and phase3 `.env` for `GROQ_API_KEY`.
- **4.3** OpenAPI docs at `/docs`.

**Deliverables:** Running API server, documented endpoint(s).

---

### Phase 5: UI for Recommendations

**Goal:** A dedicated UI page where users can submit inputs and see recommendations.

- **5.1** **UI stack:** React/Vite (Phase 5) and **Streamlit** (alternative for deployment).
- **5.2** **Recommendations page:**
  - **Input form:** Place (dropdown; area names only, e.g. BTM, Banashankari), Rating (dynamic based on location), Price range, Cuisine.
  - **Submit:** Call Phase 4 backend API.
  - **Results:** Light-themed recommendation tiles (cards) with: name, rating badge, cuisine/price/address as bullet points, "Why you'll like it" section with detailed rationale. Red centered "Get Recommendations" button.
  - **Features:** Dynamic rating dropdown showing available ratings for selected location, centered red CTA button.
- **5.3** **UX:** Loading state, error messages, empty state when no results.
- **5.4** **Deployment:** Streamlit UI deployable via Streamlit Cloud; configurable `API_BASE_URL` via `.env` or Streamlit secrets. Footer: Zomato-AI-Recommender © 2026 Ashish Kumar Sankhua.

**Deliverables:** React UI (localhost:5173), Streamlit UI (localhost:5175), deployment guide in DEPLOYMENT.md.

---

## 7. End-to-End Data Flow (Summary)

1. **User** enters Place, Rating, and optionally Price and Cuisine in the UI.
2. **UI** sends these to the Backend API (or server-side handler).
3. **Backend** loads (or uses cached) **cleaned data** from the Data Cleaning Pipeline (fed by Hugging Face dataset).
4. **Backend** **filters** cleaned data by place, rating, price, cuisine.
5. **Backend** builds an **LLM prompt** with user inputs + candidate restaurants and calls the **LLM**.
6. **LLM** returns ranked/summarized recommendations (and optionally short reasoning).
7. **Backend** parses and returns **structured recommendations** to the UI.
8. **UI** **displays** recommendations (and any error/empty states).

---

## 8. Technology Stack

- **Language:** Python for data processing, filtering, and LLM service.
- **Data:** Pre-loaded CSV (~1000 rows, 29 locations, 63 cuisines).
- **LLM:** Groq API (`groq` client); fallback to filtered results when API unavailable.
- **Backend API:** FastAPI; CORS enabled; loads root `.env` and phase3 `.env`.
- **UI:** React/Vite (Phase 5) and **Streamlit** (deployment); both call Phase 4 API.
- **Config:** Root `.env` for `GROQ_API_KEY`, `API_BASE_URL`, etc.; `.env.example` as template. Streamlit Cloud uses Secrets.

---

## 9. Deployment

- **Streamlit Cloud:** Deploy `streamlit_app.py`; set `API_BASE_URL` in Secrets to point at deployed backend.
- **Backend:** Deploy Phase 4 API (e.g. Render, Railway) with `CLEANED_DATA_PATH` and `GROQ_API_KEY`.
- See **DEPLOYMENT.md** for full instructions.

**Out of scope (current):** User accounts, auth, streaming LLM, production scaling.

---

## 10. Document Control

- **Version:** 1.3  
- **Purpose:** Architecture document; reflects current implementation.  
- **Last updated:** March 2026
- **Recent updates:**
  - Optimized dataset: ~1000 rows (from 51k), 29 locations, 63 cuisines, 172KB CSV.
  - Removed Hugging Face runtime dependency; data pre-loaded in CSV.
  - Added dynamic rating filter based on selected location.
  - UI improvements: centered red button, streamlined CSS.
  - Performance: <1s startup, instant recommendations.

---

## 11. Integration & End-to-End

- **Data loading:** `phase4/src/data_loader.py` loads CSV from `phase4/data/cleaned.csv` at startup.
- **Phase 4:** Loads CSV once; GET `/locations` uses only `listed_in(city)` and `location` (area names).
- **Phase 4 → Phase 3:** `recommendation_service.py` calls Phase 3 `get_recommendations`. Fallback when `GROQ_API_KEY` missing.
- **Streamlit UI:** `streamlit run streamlit_app.py`; reads `API_BASE_URL` from `.env` or Streamlit secrets.
- **Dynamic ratings:** `get_ratings_for_location()` filters ratings based on selected location.
- **Performance:** CSV loads in <1s; recommendations generated instantly.
