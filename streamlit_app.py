"""
Zomato AI Recommender - Streamlit Frontend

Works in two modes:
- API mode (local): Uses Phase 4 backend when API_BASE_URL is reachable.
- Standalone mode (Streamlit Cloud): Embeds Phase 3+4 logic, no separate backend needed.
"""

import html
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

import streamlit as st

# Add repo root for standalone mode imports (phase4.src, phase3.src)
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    import requests
except ImportError:
    requests = None

# --- Configuration ---
# Streamlit Cloud: set GROQ_API_KEY (and optionally API_BASE_URL) in Secrets.
def _inject_secrets_to_env():
    """Inject Streamlit secrets into os.environ for Phase 3 (GROQ_API_KEY)."""
    try:
        if hasattr(st, "secrets") and st.secrets:
            for key in ("GROQ_API_KEY",):
                if st.secrets.get(key) and not os.environ.get(key):
                    os.environ[key] = str(st.secrets[key])
    except Exception:
        pass


# Streamlit Cloud: set API_BASE_URL in Secrets. Local: use .env or env var.
def _get_api_base_url() -> str:
    try:
        if hasattr(st, "secrets") and st.secrets.get("API_BASE_URL"):
            return str(st.secrets["API_BASE_URL"]).rstrip("/")
    except Exception:
        pass
    return os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")

RATING_OPTIONS = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]

# Fallback when API is unreachable or returns empty (Bangalore areas & common cuisines)
FALLBACK_LOCALITIES = [
    "BTM Layout", "Koramangala", "Indiranagar", "Whitefield", "Jayanagar",
    "HSR Layout", "Malleshwaram", "Marathahalli", "JP Nagar", "Banashankari",
    "MG Road", "Electronic City", "Basavanagudi", "Ulsoor", "Frazer Town",
]
FALLBACK_CUISINES = [
    "North Indian", "South Indian", "Chinese", "Continental", "Italian",
    "Cafe", "Fast Food", "Bakery", "Desserts", "Street Food",
]

PRICE_RANGES = [
    ("", "Select price range..."),
    ("0-300", "Up to ₹300"),
    ("300-600", "₹300 - ₹600"),
    ("600-900", "₹600 - ₹900"),
    ("900-1200", "₹900 - ₹1200"),
    ("1200-1500", "₹1200 - ₹1500"),
    ("1500-2000", "₹1500 - ₹2000"),
    ("2000-99999", "₹2000+"),
]


# --- Standalone mode (embedded backend logic, no API) ---
_CLEANED_ROWS: List[Dict[str, Any]] = []
_GET_RECOMMENDATIONS = None


@st.cache_data(ttl=3600)  # Cache for 1 hour
def _load_standalone_data() -> List[Dict[str, Any]]:
    """Load cleaned data from bundled CSV."""
    global _CLEANED_ROWS
    if _CLEANED_ROWS:
        return _CLEANED_ROWS
    
    csv_path = REPO_ROOT / "phase4" / "data" / "cleaned.csv"
    if csv_path.exists():
        try:
            from phase4.src.data_loader import load_cleaned_data
            _CLEANED_ROWS = load_cleaned_data(path=str(csv_path))
        except Exception:
            pass
    return _CLEANED_ROWS


def _get_locations_from_data(rows: List[Dict[str, Any]]) -> List[str]:
    """Extract unique area names from listed_in(city) for clean dropdown."""
    seen = set()
    for r in rows:
        val = r.get("listed_in(city)")
        if val and str(val).strip():
            seen.add(str(val).strip())
    return sorted(seen)


def _get_cuisines_from_data(rows: List[Dict[str, Any]]) -> List[str]:
    """Extract unique cuisines from loaded data."""
    seen = set()
    for r in rows:
        for c in (r.get("cuisines") or []):
            if c and str(c).strip():
                seen.add(str(c).strip())
    return sorted(seen)


def _recommendations_standalone(
    place: str, rating: float, price: Optional[int] = None, min_price: Optional[int] = None, cuisine: Optional[str] = None
) -> Dict[str, Any]:
    """Call Phase 3/4 recommendation logic directly (no HTTP)."""
    rows = _load_standalone_data()
    if not rows:
        return {"recommendations": [], "raw_response": "", "summary": "No data loaded.", "candidates_count": 0}
    try:
        from phase4.src.recommendation_service import get_recommendations
        return get_recommendations(rows, place=place, rating=rating, price=price, min_price=min_price, cuisine=cuisine)
    except Exception as e:
        return {
            "recommendations": [],
            "raw_response": "",
            "summary": str(e),
            "candidates_count": 0,
        }


# --- API Client (matches phase5/src/api.js) ---
def api_url(path: str) -> str:
    base = _get_api_base_url()
    return f"{base}{path}"


def fetch_locations() -> List[str]:
    """Fetch unique locations from backend (GET /locations)."""
    if not requests:
        raise RuntimeError("requests not installed")
    r = requests.get(api_url("/locations"), timeout=10)
    r.raise_for_status()
    data = r.json()
    return data.get("locations", []) if isinstance(data.get("locations"), list) else []


def fetch_cuisines() -> List[str]:
    """Fetch unique cuisines from backend (GET /cuisines)."""
    if not requests:
        raise RuntimeError("requests not installed")
    r = requests.get(api_url("/cuisines"), timeout=10)
    r.raise_for_status()
    data = r.json()
    return data.get("cuisines", []) if isinstance(data.get("cuisines"), list) else []


def fetch_recommendations(
    place: str, rating: float, price: Optional[int] = None, min_price: Optional[int] = None, cuisine: Optional[str] = None
) -> Dict[str, Any]:
    """POST /recommendations - same contract as phase5 api.js."""
    body = {"place": place.strip(), "rating": float(rating)}
    if price is not None and price > 0:
        body["price"] = int(price)
    if min_price is not None and min_price >= 0:
        body["min_price"] = int(min_price)
    if cuisine and str(cuisine).strip():
        body["cuisine"] = str(cuisine).strip()
    r = requests.post(api_url("/recommendations"), json=body, timeout=60)
    r.raise_for_status()
    data = r.json()
    recs = data.get("recommendations") or []
    return {
        "recommendations": [
            {
                "name": rec.get("name", "Unknown"),
                "reason": rec.get("reason", ""),
                "rating": rec.get("rating"),
                "cuisine": rec.get("cuisine", "") or "",
                "price": rec.get("price"),
                "address": rec.get("address", "") or "",
            }
            for rec in recs
        ],
        "raw_response": data.get("raw_response", ""),
        "summary": data.get("summary", ""),
        "candidates_count": data.get("candidates_count", 0),
    }


# --- CSS (matches phase5/src/index.css) ---
STYLES = """
<style>
/* Zomato AI Recommender - Light Theme */
.stApp { max-width: 1200px; margin: 0 auto; }
div[data-testid="stAppViewContainer"] { background: linear-gradient(180deg, #f5f5f5 0%, #fafafa 50%, #f0f0f0 100%); }

.main-header { text-align: center; margin-bottom: 2rem; }
.app-title { font-size: 2.5rem; font-weight: 800; color: #1a1a1a; margin-bottom: 0.5rem; letter-spacing: -0.02em; }
.title-accent { color: #ff4757; }
.app-subtitle { font-size: 1.05rem; color: #444; margin-bottom: 1.25rem; font-weight: 400; }
.app-stats { display: flex; align-items: center; justify-content: center; gap: 0.75rem; font-size: 1rem; color: #444; }
.stat-item strong { color: #ff4757; }
.stat-sep { color: #999; font-weight: 300; margin: 0 0.25rem; }

.form-section { margin-bottom: 2rem; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
@media (max-width: 640px) { .form-row { grid-template-columns: 1fr; } }

.results-section { background: #fff; border: 1px solid #e0e0e0; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.loading-state { display: flex; flex-direction: column; align-items: center; gap: 1rem; padding: 2rem; }
.loading-state p { color: #555; font-size: 0.95rem; }
.empty-state { text-align: center; padding: 2rem 1rem; }
.empty-msg { color: #555; font-size: 0.95rem; }
.empty-hint { color: #666; font-size: 0.9rem; margin-top: 0.75rem; }
.error-section { border-color: #ff4757; }
.error-msg { color: #ff6b6b; }

.results-summary { background: #f8f9fa; border: 1px solid #e8e8e8; border-radius: 12px; padding: 1.25rem 1.5rem; color: #333; font-size: 1rem; line-height: 1.6; margin-bottom: 1.5rem; }
.rec-tiles { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.25rem; }
@media (max-width: 640px) { .rec-tiles { grid-template-columns: 1fr; } }
.rec-tile { background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 50%, #f1f3f5 100%); border: 1px solid #e9ecef; border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.rec-tile-header { display: flex; justify-content: space-between; align-items: center; gap: 0.75rem; margin-bottom: 1rem; }
.rec-tile-name { font-size: 1.35rem; font-weight: 700; color: #1a1a1a; margin: 0; flex: 1; }
.rec-tile-rating { background: #5cb85c; color: #fff; font-size: 0.9rem; font-weight: 600; padding: 0.35rem 0.75rem; border-radius: 20px; flex-shrink: 0; }
.rec-tile-details { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1rem; }
.rec-tile-row { display: flex; align-items: flex-start; gap: 0.5rem; font-size: 0.95rem; color: #495057; line-height: 1.5; }
.rec-tile-why { background: #f1f3f5; border-left: 4px solid #FF4C4C; border-radius: 0 8px 8px 0; padding: 1rem 1.25rem; margin-top: 0; }
.rec-tile-why-title { font-weight: 700; color: #1a1a1a; font-size: 0.95rem; margin-bottom: 0.5rem; }
.rec-tile-why-text { color: #495057; font-size: 0.9rem; line-height: 1.6; font-style: italic; margin: 0; }

.app-footer { text-align: center; padding: 2.5rem 1rem; font-size: 0.85rem; color: #6c757d; line-height: 1.6; }
.app-footer-brand { font-weight: 600; color: #1a1a1a; letter-spacing: 0.05em; }

.stButton > button { width: 100%; max-width: 400px; background: #e23744 !important; background-color: #e23744 !important; color: white !important; font-weight: 600; padding: 1rem 1.5rem; border-radius: 10px; border: none; margin-left: auto; margin-right: auto; display: block; text-align: center; }
.stButton > button:hover { background: #c41e2a !important; background-color: #c41e2a !important; box-shadow: 0 4px 20px rgba(226, 55, 68, 0.5); color: white !important; }
</style>
"""


# --- Page config ---
st.set_page_config(
    page_title="Zomato AI Recommender",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(STYLES, unsafe_allow_html=True)

_inject_secrets_to_env()

# --- Header ---
st.markdown("""
<div class="main-header">
  <h1 class="app-title">Zomato AI <span class="title-accent">Recommender</span></h1>
  <p class="app-subtitle">Helping you find the best places to eat in Bangalore city</p>
</div>
""", unsafe_allow_html=True)

# --- Load locations & cuisines ---
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_options():
    """Fetch from API when available; otherwise use bundled data."""
    locs, cuis = [], []
    try:
        locs = fetch_locations()
        cuis = fetch_cuisines()
    except Exception:
        # API failed, use bundled data
        rows = _load_standalone_data()
        if rows:
            locs = _get_locations_from_data(rows)
            cuis = _get_cuisines_from_data(rows)
    if not locs:
        locs = FALLBACK_LOCALITIES
    if not cuis:
        cuis = FALLBACK_CUISINES
    return locs, cuis


@st.cache_data(ttl=3600)
def get_ratings_for_location(location: str) -> List[float]:
    """Get available ratings for a specific location."""
    rows = _load_standalone_data()
    ratings = set()
    for r in rows:
        if r.get("listed_in(city)") == location or r.get("location") == location:
            rating = r.get("rating")
            if rating:
                ratings.add(float(rating))
    return sorted(ratings) if ratings else RATING_OPTIONS


# Load options (with spinner on first load)
with st.spinner("Loading options..."):
    locations, cuisines = load_options()

# Ensure we never show 0 (fallback if cache or API returns empty)
locations = locations or FALLBACK_LOCALITIES
cuisines = cuisines or FALLBACK_CUISINES

st.markdown(f"""
<div class="app-stats">
  <span class="stat-item">📍 <strong>{len(locations)}</strong> Localities</span>
  <span class="stat-sep">|</span>
  <span class="stat-item">👨‍🍳 <strong>{len(cuisines)}</strong> Cuisines</span>
</div>
""", unsafe_allow_html=True)



# --- Form (same layout as Phase 5) ---
st.markdown('<div class="form-section">', unsafe_allow_html=True)

# Get selected location for dynamic rating
selected_location = st.session_state.get("locality_select", "Select locality...")
if selected_location != "Select locality...":
    available_ratings = get_ratings_for_location(selected_location)
else:
    available_ratings = RATING_OPTIONS

with st.form("recommendation_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
        place_options = ["Select locality..."] + locations
        place = st.selectbox(
            "📍 Select locality *",
            options=place_options,
            index=0,
            key="locality_select",
        )
        place = "" if place == "Select locality..." else place

        cuisine_options = ["Select cuisines..."] + cuisines
        cuisine = st.selectbox(
            "👨‍🍳 Cuisines",
            options=cuisine_options,
            index=0,
            key="cuisine_select",
        )
        cuisine = "" if cuisine == "Select cuisines..." else cuisine

    with col2:
        price_options = [pv for pv, _ in PRICE_RANGES]
        price_idx = st.selectbox(
            "💰 Price Range",
            range(len(PRICE_RANGES)),
            format_func=lambda i: PRICE_RANGES[i][1],
        )
        price_val = price_options[price_idx]

        # Dynamic rating based on location
        rating_label = f"⭐ Min Rating ({len(available_ratings)} options)" if place else "⭐ Min Rating"
        rating = st.selectbox(
            rating_label,
            options=available_ratings,
            index=min(4, len(available_ratings)-1) if available_ratings else 0,
        )

    # Center the submit button
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        submitted = st.form_submit_button("Get Recommendations ✨")

st.markdown("</div>", unsafe_allow_html=True)

# --- Handle submit ---
if submitted:
    place_trim = place.strip() if place else ""
    if not place_trim:
        st.error("Please select a locality.")
    else:
        min_price = None
        max_price = None
        if price_val and price_val.strip() and "-" in price_val:
            try:
                parts = price_val.split("-")
                min_price = int(parts[0]) if parts[0] else None
                max_price = int(parts[1]) if parts[1] else None
            except ValueError:
                pass

        with st.spinner("AI is analyzing restaurants for you..."):
            result = None
            try:
                if requests:
                    result = fetch_recommendations(
                        place=place_trim,
                        rating=float(rating),
                        price=max_price,
                        min_price=min_price,
                        cuisine=cuisine.strip() if cuisine else None,
                    )
            except Exception as e:
                if requests and isinstance(e, requests.RequestException):
                    err = str(e) or ""
                    if "Connection" in err or "fetch" in err.lower() or "refused" in err.lower():
                        result = _recommendations_standalone(
                            place=place_trim,
                            rating=float(rating),
                            price=max_price,
                            min_price=min_price,
                            cuisine=cuisine.strip() if cuisine else None,
                        )
                if result is None:
                    st.error(str(e) or "Failed to load recommendations.")

            if result:
                if result["recommendations"]:
                    summary = result.get("summary") or ""
                    if summary and "LLM disabled" not in summary and "GROQ_API_KEY" not in summary:
                        st.info(summary)
                    # Recommendation tiles: dark-themed card matching reference design
                    recs = result["recommendations"]
                    for i in range(0, len(recs), 2):
                        cols = st.columns(2, gap="large")
                        if i > 0:
                            st.markdown("")
                        for j, col in enumerate(cols):
                            if i + j < len(recs):
                                rec = recs[i + j]
                                name_esc = html.escape(str(rec.get("name", "Unknown")))
                                reason_esc = html.escape(str(rec.get("reason", "")))
                                cuisine_esc = html.escape(str(rec.get("cuisine", "")))
                                addr_esc = html.escape(str(rec.get("address", "")))
                                rating_val = rec.get("rating")
                                price_val = rec.get("price")
                                rating_html = f'<span class="rec-tile-rating">⭐ {rating_val}</span>' if rating_val is not None else ""
                                cuisine_html = f'<div class="rec-tile-row">🍴 {cuisine_esc}</div>' if rec.get("cuisine") else ""
                                price_html = f'<div class="rec-tile-row">💰 Avg. ₹{price_val} for two</div>' if price_val and int(price_val) > 0 else ""
                                addr_html = f'<div class="rec-tile-row">📍 {addr_esc}</div>' if rec.get("address") else ""
                                tile_html = f'''
                                <div class="rec-tile">
                                  <div class="rec-tile-header">
                                    <h3 class="rec-tile-name">{name_esc}</h3>
                                    {rating_html}
                                  </div>
                                  <div class="rec-tile-details">
                                    {cuisine_html}
                                    {price_html}
                                    {addr_html}
                                  </div>
                                  <div class="rec-tile-why">
                                    <div class="rec-tile-why-title">Why you'll like it:</div>
                                    <p class="rec-tile-why-text">{reason_esc}</p>
                                  </div>
                                </div>
                                '''
                                with col:
                                    st.markdown(tile_html, unsafe_allow_html=True)
                else:
                    st.warning("No recommendations found for your criteria.")
                    st.caption("Try lowering the minimum rating (most restaurants are below 5.0) or relaxing the price range.")

# --- Footer ---
st.markdown("""
<footer class="app-footer">
  <div class="app-footer-brand">Zomato-AI-Recommender</div>
  <div>© 2026 Ashish Kumar Sankhua. All rights reserved.</div>
</footer>
""", unsafe_allow_html=True)
