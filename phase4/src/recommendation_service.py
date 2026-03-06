"""
Recommendation service wrapper: use Phase 3 when available, else stub.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

def _get_phase3_get_recommendations():
    """Import Phase 3 get_recommendations. Requires phase3 on PYTHONPATH before phase4."""
    try:
        root = Path(__file__).resolve().parent.parent.parent
        phase3 = root / "phase3"
        if phase3.exists() and str(phase3) not in sys.path:
            sys.path.insert(0, str(phase3))
        from src.service import get_recommendations
        return get_recommendations
    except Exception:
        return None

_get_recommendations_impl = _get_phase3_get_recommendations()


def get_recommendations(
    cleaned_rows: List[Dict[str, Any]],
    place: str,
    rating: float,
    price: Optional[int] = None,
    min_price: Optional[int] = None,
    cuisine: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Call Phase 3 get_recommendations if available; otherwise return empty result."""
    if _get_recommendations_impl is not None:
        return _get_recommendations_impl(
            cleaned_rows, place=place, rating=rating, price=price, min_price=min_price, cuisine=cuisine, **kwargs
        )
    return {
        "recommendations": [],
        "raw_response": "Recommendation service (Phase 3) not available.",
        "summary": "",
        "candidates_count": 0,
    }
