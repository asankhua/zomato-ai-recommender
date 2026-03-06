"""
Phase 4: Backend API for restaurant recommendations.

Run with: uvicorn src.app:app --reload
"""

import os
from pathlib import Path

# Load env: root .env first, then phase3/.env (root overrides)
_root = Path(__file__).resolve().parent.parent.parent
_root_env = _root / ".env"
_phase3_env = _root / "phase3" / ".env"
from dotenv import load_dotenv
if _root_env.exists():
    load_dotenv(_root_env)
if _phase3_env.exists():
    load_dotenv(_phase3_env)

from typing import List, Optional

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .data_loader import load_cleaned_data
from .recommendation_service import get_recommendations

api = APIRouter()


# Load cleaned data once at startup (optional: set CLEANED_DATA_PATH)
CLEANED_ROWS = load_cleaned_data()


app = FastAPI(
    title="Zomato AI Restaurant Recommendation API",
    description="Submit place, rating, and optional price/cuisine to get LLM-powered recommendations.",
    version="1.0.0",
)

# CORS: allow UI (Phase 5) to call from different origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class RecommendationRequest(BaseModel):
    """Request body for POST /recommendations."""

    place: str = Field(..., min_length=1, description="Location/place (mandatory)")
    rating: float = Field(..., ge=0, le=5, description="Minimum rating 0-5 (mandatory)")
    price: Optional[int] = Field(None, ge=0, description="Max price for two (optional)")
    min_price: Optional[int] = Field(None, ge=0, description="Min price for two (optional)")
    cuisine: Optional[str] = Field(None, description="Preferred cuisine (optional)")


class RecommendationItem(BaseModel):
    name: str
    reason: str
    rating: Optional[float] = None
    cuisine: Optional[str] = None
    price: Optional[int] = None
    address: Optional[str] = None


class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationItem]
    raw_response: str
    summary: Optional[str] = None
    candidates_count: int


@app.get("/")
def root():
    """Root: link to docs and endpoints."""
    return {
        "message": "Zomato AI Restaurant Recommendation API",
        "docs": "/docs",
        "endpoints": ["/health", "/locations", "/cuisines", "/recommendations"],
    }


@app.get("/health")
def health():
    """Health check."""
    return {"status": "ok"}


@app.get("/locations")
def get_locations():
    return _get_locations()


@api.get("/health")
def _health():
    return {"status": "ok"}


@api.get("/locations")
def _get_locations():
    """Return unique area names (BTM, Banashankari, etc.) for dropdown."""
    seen = set()
    for r in CLEANED_ROWS:
        for key in ("listed_in(city)", "location"):
            val = r.get(key)
            if val and str(val).strip():
                seen.add(str(val).strip())
    return {"locations": sorted(seen)}


@api.get("/cuisines")
def _get_cuisines():
    """Return unique cuisines from cleaned data for dropdown."""
    seen = set()
    for r in CLEANED_ROWS:
        for c in (r.get("cuisines") or []):
            if c and c.strip():
                seen.add(c.strip())
    return {"cuisines": sorted(seen)}


def _recommendations_post(request: RecommendationRequest):
    result = get_recommendations(
        CLEANED_ROWS,
        place=request.place.strip(),
        rating=request.rating,
        price=request.price,
        min_price=request.min_price,
        cuisine=request.cuisine.strip() if request.cuisine else None,
    )
    return RecommendationResponse(
        recommendations=[
            RecommendationItem(
                name=r["name"],
                reason=r["reason"],
                rating=r.get("rating"),
                cuisine=r.get("cuisine"),
                price=r.get("price"),
                address=r.get("address"),
            )
            for r in result["recommendations"]
        ],
        raw_response=result["raw_response"],
        summary=result.get("summary"),
        candidates_count=result["candidates_count"],
    )


@api.post("/recommendations", response_model=RecommendationResponse)
def api_recommendations_post(request: RecommendationRequest):
    return _recommendations_post(request)


@api.get("/recommendations", response_model=RecommendationResponse)
def api_recommendations_get(
    place: str,
    rating: float,
    price: Optional[int] = None,
    min_price: Optional[int] = None,
    cuisine: Optional[str] = None,
):
    if not place or not place.strip():
        raise HTTPException(status_code=400, detail="place is required")
    if rating is None or rating < 0 or rating > 5:
        raise HTTPException(status_code=400, detail="rating must be between 0 and 5")
    result = get_recommendations(
        CLEANED_ROWS,
        place=place.strip(),
        rating=float(rating),
        price=price,
        min_price=min_price,
        cuisine=cuisine.strip() if cuisine else None,
    )
    return RecommendationResponse(
        recommendations=[
            RecommendationItem(
                name=r["name"],
                reason=r["reason"],
                rating=r.get("rating"),
                cuisine=r.get("cuisine"),
                price=r.get("price"),
                address=r.get("address"),
            )
            for r in result["recommendations"]
        ],
        raw_response=result["raw_response"],
        summary=result.get("summary"),
        candidates_count=result["candidates_count"],
    )


@app.get("/cuisines")
def get_cuisines():
    return _get_cuisines()


@app.post("/recommendations", response_model=RecommendationResponse)
def recommendations(request: RecommendationRequest):
    return _recommendations_post(request)


@app.get("/recommendations", response_model=RecommendationResponse)
def recommendations_get(
    place: str,
    rating: float,
    price: Optional[int] = None,
    min_price: Optional[int] = None,
    cuisine: Optional[str] = None,
):
    """GET variant: place and rating as query params."""
    if not place or not place.strip():
        raise HTTPException(status_code=400, detail="place is required")
    if rating is None or rating < 0 or rating > 5:
        raise HTTPException(status_code=400, detail="rating must be between 0 and 5")
    return api_recommendations_get(place, rating, price, min_price, cuisine)


# Mount /api/* routes so clients using /api prefix get the same endpoints
app.include_router(api, prefix="/api")
