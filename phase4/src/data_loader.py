"""
Load cleaned restaurant data from CSV (optional). Used to populate data for recommendations.
"""

import csv
import os

# Allow large CSV fields (e.g. reviews_list in Zomato dataset)
csv.field_size_limit(10**7)
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_cleaned_data(path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load cleaned rows from a CSV file.

    CSV should have columns compatible with Phase 3 (e.g. location, name, rating, price, cuisines).
    cuisines can be comma-separated in the CSV; we parse back to list.

    Args:
        path: File path. If None, uses env CLEANED_DATA_PATH. If still None, returns [].

    Returns:
        List of dicts (e.g. for get_recommendations).
    """
    path = path or os.environ.get("CLEANED_DATA_PATH")
    if not path or not Path(path).exists():
        return []

    rows: List[Dict[str, Any]] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse cuisines back to list if present
            if "cuisines" in row and row["cuisines"]:
                row["cuisines"] = [s.strip() for s in row["cuisines"].split(",") if s.strip()]
            else:
                row["cuisines"] = []
            # Ensure numeric fields
            for key in ("rating", "price"):
                if key in row and row[key]:
                    try:
                        if key == "price":
                            row[key] = int(float(row[key]))
                        else:
                            row[key] = float(row[key])
                    except (ValueError, TypeError):
                        row[key] = None if key == "price" else None
            # Normalize for Phase 3: ensure "location" and "name" exist (filter/prompt keys)
            if not row.get("location") and row.get("city"):
                row["location"] = row["city"]
            if not row.get("location") and row.get("address"):
                row["location"] = row["address"]
            if not row.get("name") and row.get("restaurant name"):
                row["name"] = row["restaurant name"]
            rows.append(row)
    return rows
