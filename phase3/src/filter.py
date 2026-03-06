"""
Filtering layer: reduce cleaned restaurant rows by place, rating, price, cuisine.
"""

from typing import Any, Dict, List, Optional


def filter_by_criteria(
    cleaned_rows: List[Dict[str, Any]],
    place: str,
    min_rating: float,
    max_price: Optional[int] = None,
    min_price: Optional[int] = None,
    cuisine: Optional[str] = None,
    place_column: str = "location",
    max_candidates: int = 50,
) -> List[Dict[str, Any]]:
    """
    Filter cleaned rows by user criteria.

    Args:
        cleaned_rows: List of clean records (each has "rating", "price", "cuisines"
            and a place-like column).
        place: Mandatory. Match rows where place_column contains this (case-insensitive).
        min_rating: Mandatory. Keep only rows with rating >= this.
        max_price: Optional. Keep only rows with price <= this (None = no filter).
        min_price: Optional. Keep only rows with price >= this (None = no filter).
        cuisine: Optional. Keep only rows whose cuisines list contains this (case-insensitive).
        place_column: Key in each row for location (e.g. "location", "city", "address").
        max_candidates: Cap number of rows returned (for LLM context size).

    Returns:
        Filtered list of rows, up to max_candidates.
    """
    place_clean = (place or "").strip().lower()
    if not place_clean:
        return []

    out: List[Dict[str, Any]] = []
    for row in cleaned_rows:
        if not _passes_place(row, place_column, place_clean):
            continue
        if not _passes_rating(row, min_rating):
            continue
        if not _passes_price_range(row, min_price, max_price):
            continue
        if cuisine is not None and cuisine.strip() and not _passes_cuisine(row, cuisine.strip()):
            continue
        out.append(row)
        if len(out) >= max_candidates:
            break

    return out


def _passes_place(row: Dict[str, Any], place_column: str, place_query: str) -> bool:
    """Match place_query against location or listed_in(city) for broader coverage."""
    val = row.get(place_column)
    if val and place_query in str(val).lower():
        return True
    # Zomato dataset: listed_in(city) groups areas (e.g. Basavanagudi under Banashankari)
    city_val = row.get("listed_in(city)")
    if city_val and place_query in str(city_val).lower():
        return True
    return False


def _passes_rating(row: Dict[str, Any], min_rating: float) -> bool:
    r = row.get("rating")
    if r is None:
        return False
    try:
        return float(r) >= min_rating
    except (TypeError, ValueError):
        return False


def _passes_price_range(row: Dict[str, Any], min_price: Optional[int], max_price: Optional[int]) -> bool:
    """Check if row's price is within the specified range."""
    p = row.get("price")
    if p is None:
        # No price info: include only if no price filter is set
        return min_price is None and max_price is None
    try:
        price_val = int(p)
        if min_price is not None and price_val < min_price:
            return False
        if max_price is not None and price_val > max_price:
            return False
        return True
    except (TypeError, ValueError):
        # Invalid price: include only if no price filter is set
        return min_price is None and max_price is None


def _passes_cuisine(row: Dict[str, Any], cuisine: str) -> bool:
    cuisines = row.get("cuisines")
    if not isinstance(cuisines, list):
        return False
    c_lower = cuisine.lower()
    return any(c_lower in str(c).lower() for c in cuisines)
