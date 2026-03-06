"""
Recommendation service: single entrypoint (place, rating, price?, cuisine?) -> recommendations.
"""

import os
import re
from typing import Any, Dict, List, Optional

from .filter import filter_by_criteria
from .groq_client import get_completion
from .prompts import build_recommendation_prompt, system_prompt


def _fallback_recommendations(
    candidates: List[Dict[str, Any]],
    top_n: int,
    name_key: str = "name",
) -> List[Dict[str, Any]]:
    """Return top N candidates by rating when LLM is unavailable."""
    sorted_candidates = sorted(
        candidates,
        key=lambda r: (float(r["rating"]) if r.get("rating") is not None else 0.0),
        reverse=True,
    )[:top_n]
    out = []
    for c in sorted_candidates:
        name = (c.get(name_key) or c.get("restaurant name") or "Restaurant").strip()
        rating = c.get("rating")
        cuis = c.get("cuisines") or []
        cuisine_str = ", ".join(str(x) for x in cuis) if isinstance(cuis, list) else str(cuis or "")
        reason_parts = []
        price_val = c.get("price")
        price_int = int(price_val) if price_val is not None else 0
        if rating is not None and cuisine_str:
            reason_parts.append(
                f"This restaurant is a great match for someone looking for {cuisine_str} cuisine, "
                f"with a rating of {rating}/5"
            )
            if price_int > 0:
                reason_parts.append(f" and a budget-friendly price of ₹{price_int} for two. ")
            else:
                reason_parts.append(". ")
            reason_parts.append(
                "It meets your criteria and is an excellent choice for your next meal."
            )
        else:
            if rating is not None:
                reason_parts.append(f"Rated {rating}/5 by diners—a top choice in the area. ")
            if cuisine_str:
                reason_parts.append(f"Serves {cuisine_str}. ")
            if price_int > 0:
                reason_parts.append(f"Approx ₹{price_int} for two—good value.")
        reason = "".join(reason_parts)
        out.append({
            "name": name,
            "reason": reason,
            "rating": float(rating) if rating is not None else None,
            "cuisine": cuisine_str,
            "price": int(c["price"]) if c.get("price") is not None else None,
            "address": str(c.get("address") or c.get("location") or ""),
        })
    return out


def get_recommendations(
    cleaned_rows: List[Dict[str, Any]],
    place: str,
    rating: float,
    price: Optional[int] = None,
    min_price: Optional[int] = None,
    cuisine: Optional[str] = None,
    place_column: str = "location",
    name_key: str = "name",
    max_candidates: int = 50,
    top_n: int = 5,
    model: str = "llama-3.3-70b-versatile",
) -> Dict[str, Any]:
    """
    Filter cleaned data by criteria, call Groq LLM, and return structured recommendations.

    Args:
        cleaned_rows: Output from Phase 2 run_pipeline (or list of dicts with
            "rating", "price", "cuisines" and a place column).
        place: Mandatory location filter.
        rating: Mandatory minimum rating.
        price: Optional max price for two.
        min_price: Optional min price for two.
        cuisine: Optional cuisine preference.
        place_column: Key for location in each row.
        name_key: Key for restaurant name in each row.
        max_candidates: Max rows to send to LLM.
        top_n: Number of recommendations to request.
        model: Groq model id.

    Returns:
        Dict with:
          - "recommendations": list of {"name": str, "reason": str} (parsed from LLM),
          - "raw_response": full LLM text (if parsing fails or for display),
          - "candidates_count": number of restaurants passed to the LLM.
    """
    candidates = filter_by_criteria(
        cleaned_rows,
        place=place,
        min_rating=rating,
        max_price=price,
        min_price=min_price,
        cuisine=cuisine,
        place_column=place_column,
        max_candidates=max_candidates,
    )

    if not candidates:
        return {
            "recommendations": [],
            "raw_response": "No matching restaurants found for your criteria.",
            "candidates_count": 0,
        }

    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        # No API key: return top candidates with generic reasons
        enriched = _fallback_recommendations(candidates, top_n, name_key=name_key)
        return {
            "recommendations": enriched,
            "raw_response": "(Add GROQ_API_KEY to .env for AI-powered recommendations)",
            "summary": f"Top {len(enriched)} restaurants matching your criteria (LLM disabled—add GROQ_API_KEY to .env for AI recommendations).",
            "candidates_count": len(candidates),
        }

    user_prompt = build_recommendation_prompt(
        place=place,
        min_rating=rating,
        max_price=price,
        cuisine=cuisine,
        candidates=candidates,
        top_n=top_n,
        name_key=name_key,
    )
    sys_prompt = system_prompt()

    try:
        raw_response = get_completion(
            user_prompt=user_prompt,
            system_prompt=sys_prompt,
            model=model,
        )
    except (ValueError, Exception):
        # API key invalid or Groq API error: fall back to filtered results
        enriched = _fallback_recommendations(candidates, top_n, name_key=name_key)
        return {
            "recommendations": enriched,
            "raw_response": "(Groq API unavailable—showing filtered results. Check GROQ_API_KEY in .env.)",
            "summary": f"Top {len(enriched)} restaurants matching your criteria.",
            "candidates_count": len(candidates),
        }

    recommendations = _parse_recommendations(raw_response)
    enriched = _enrich_with_candidate_data(recommendations, candidates, name_key=name_key)
    summary = _extract_summary(raw_response, enriched)
    return {
        "recommendations": enriched,
        "raw_response": raw_response,
        "summary": summary,
        "candidates_count": len(candidates),
    }


def _extract_summary(raw_response: str, recommendations: List[Dict[str, Any]]) -> str:
    """Extract intro paragraph before the numbered/bullet list."""
    if not raw_response or not raw_response.strip():
        return ""
    match = re.search(r"^[\s]*[-*\d.]+\s*(.+?):\s*(.+)$", raw_response, re.MULTILINE)
    if match:
        intro = raw_response[: match.start()].strip()
        if intro and len(intro) > 20:
            return intro
    return raw_response.split("\n")[0].strip() if raw_response else ""


def _enrich_with_candidate_data(
    recommendations: List[Dict[str, Any]],
    candidates: List[Dict[str, Any]],
    name_key: str = "name",
) -> List[Dict[str, Any]]:
    """Match each recommendation to a candidate and add rating, cuisines, price, address."""
    out = []
    name_to_candidates = {}
    for c in candidates:
        n = (c.get(name_key) or c.get("restaurant name") or "").strip()
        if n and n not in name_to_candidates:
            name_to_candidates[n.lower()] = c
    for rec in recommendations:
        name = (rec.get("name") or "").strip()
        reason = rec.get("reason") or ""
        enriched = {"name": name, "reason": reason, "rating": None, "cuisine": "", "price": None, "address": ""}
        cand = None
        if name:
            cand = name_to_candidates.get(name.lower())
            if not cand:
                for k, c in name_to_candidates.items():
                    if k in name.lower() or name.lower() in k:
                        cand = c
                        break
        if cand:
            r = cand.get("rating")
            enriched["rating"] = float(r) if r is not None else None
            cuis = cand.get("cuisines")
            enriched["cuisine"] = ", ".join(cuis) if isinstance(cuis, list) else str(cuis or "")
            p = cand.get("price")
            enriched["price"] = int(p) if p is not None else None
            addr = cand.get("address") or cand.get("location") or ""
            enriched["address"] = str(addr) if addr else ""
        out.append(enriched)
    return out


def _parse_recommendations(text: str) -> List[Dict[str, str]]:
    """
    Parse LLM response into list of {name, reason}.
    Expects lines like "- <Name>: <reason>" or "1. <Name>: <reason>".
    """
    out: List[Dict[str, str]] = []
    # Match "- Restaurant Name: reason" or "1. Restaurant Name: reason"
    pattern = re.compile(r"^[\s]*[-*\d.]+\s*(.+?):\s*(.+)$", re.MULTILINE)
    for m in pattern.finditer(text):
        name = m.group(1).strip()
        reason = m.group(2).strip()
        if name and reason:
            out.append({"name": name, "reason": reason})
    if not out and text.strip():
        # Fallback: single block as one recommendation
        out.append({"name": "Recommendation", "reason": text.strip()[:500]})
    return out
