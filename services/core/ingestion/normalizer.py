"""
Ingestion Normalizer
Standardizes states, numbers, currencies, dates, and common scheme vocabulary.
"""
import re
from typing import Optional, Tuple, Dict, Any, List

STATE_SYNONYMS: Dict[str, str] = {
    "andhra pradesh": "Andhra Pradesh", "ap": "Andhra Pradesh",
    "arunachal pradesh": "Arunachal Pradesh",
    "assam": "Assam", "bihar": "Bihar", "chhattisgarh": "Chhattisgarh",
    "goa": "Goa", "gujarat": "Gujarat", "haryana": "Haryana",
    "himachal pradesh": "Himachal Pradesh", "hp": "Himachal Pradesh",
    "jharkhand": "Jharkhand", "karnataka": "Karnataka",
    "kerala": "Kerala", "madhya pradesh": "Madhya Pradesh", "mp": "Madhya Pradesh",
    "maharashtra": "Maharashtra", "manipur": "Manipur", "meghalaya": "Meghalaya",
    "mizoram": "Mizoram", "nagaland": "Nagaland", "odisha": "Odisha", "orissa": "Odisha",
    "punjab": "Punjab", "rajasthan": "Rajasthan", "sikkim": "Sikkim",
    "tamil nadu": "Tamil Nadu", "tn": "Tamil Nadu", "telangana": "Telangana",
    "tripura": "Tripura", "uttar pradesh": "Uttar Pradesh", "up": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand", "uk": "Uttarakhand", "west bengal": "West Bengal", "wb": "West Bengal",
    "delhi": "Delhi", "nct delhi": "Delhi", "jammu and kashmir": "Jammu and Kashmir", "j&k": "Jammu and Kashmir",
    "ladakh": "Ladakh", "chandigarh": "Chandigarh", "puducherry": "Puducherry"
}

def normalize_state(raw_name: str) -> Optional[str]:
    """Resolves state aliases or returns canonical state name."""
    clean = raw_name.strip().lower()
    return STATE_SYNONYMS.get(clean, raw_name.title() if len(raw_name) > 3 else None)

def parse_currency_amount(text: str) -> Optional[float]:
    """Parses expressions like '₹6,000', 'Rs. 2.5 lakh', '50,000', '1 crore' into numeric float."""
    clean = text.replace(",", "").strip()

    # Match lakh / crore
    lakh_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac)s?", clean, re.IGNORECASE)
    if lakh_match:
        return float(lakh_match.group(1)) * 100_000

    crore_match = re.search(r"(\d+(?:\.\d+)?)\s*crore?s?", clean, re.IGNORECASE)
    if crore_match:
        return float(crore_match.group(1)) * 10_000_000

    # Match plain number with optional currency symbol
    num_match = re.search(r"(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)", clean, re.IGNORECASE)
    if num_match:
        try:
            return float(num_match.group(1))
        except ValueError:
            return None
    return None

def extract_age_bounds(text: str) -> Tuple[Optional[int], Optional[int]]:
    """Extracts min and max age from strings like '18 to 40 years', 'between 21 and 60'."""
    between_match = re.search(r"(?:between|age\s*of)\s*(\d+)\s*(?:and|to|-)\s*(\d+)", text, re.IGNORECASE)
    if between_match:
        return int(between_match.group(1)), int(between_match.group(2))

    min_match = re.search(r"(?:minimum|above|at\s*least|from)\s*(?:age\s*(?:of)?)?\s*(\d+)\s*years?", text, re.IGNORECASE)
    if min_match:
        return int(min_match.group(1)), None

    max_match = re.search(r"(?:maximum|not\s*exceeding|below|up\s*to)\s*(?:age\s*(?:of)?)?\s*(\d+)\s*years?", text, re.IGNORECASE)
    if max_match:
        return None, int(max_match.group(1))

    return None, None
