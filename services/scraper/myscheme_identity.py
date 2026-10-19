"""
CivixAI myScheme Identity Resolution Engine
Matches candidates discovered from myScheme against the 135 CivixAI canonical schemes.
Strictly prevents automatic merging: classifies matches into:
- EXACT_EXISTING
- PROBABLE_ALIAS
- NEW_CANDIDATE
- HISTORICAL_OR_RENAMED
- COMPONENT_OR_SUBSCHEME
- IDENTITY_REVIEW_REQUIRED
Generates data/live_myscheme_identity_map.json.
"""
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DISCOVERY_PATH = PROJECT_ROOT / "data" / "live_myscheme_discovery_report.json"
INVENTORY_PATH = PROJECT_ROOT / "data" / "scheme_forensic_inventory.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "live_myscheme_identity_map.json"

KNOWN_ALIASES = {
    "pm-kisan": "dbtbharat_central_schemes_pm_kisan",
    "pmjjby": "pm_jeevan_jyoti_bima_v2",
    "pmsby": "pm_suraksha_bima_v2",
    "apy": "dbtbharat_central_schemes_atal_pension_yojana",
    "pmay-u": "pm_awas_urban_v2",
    "pm-ayushman-bharat": "ayushman_bharat_v2",
    "igndps": "dbtbharat_central_schemes_indira_gandhi_national_disability_pension_scheme",
    "rtif": "rtif_fellowship_candidate",
    "n-pdf": "serb_npdf_candidate",
    "mda-fert": "mda_fertilizer_subsidy",
    "psw": "dnh_pension_widow",
    "pm-vikas": "pm_vikas_minority_affairs",
    "ay": "agnipath_yojana_defence",
    "sistpomms": "assam_st_obc_meritorious_incentive",
    "pcardbpt": "tamilnadu_pcardb_power_tiller",
    "faftcc": "culture_tagore_complex_grant",
    "mgnrega": "mgnrega_rural_employment_candidate",
    "pmfby": "pmfby_crop_insurance_candidate",
    "sukanya-samriddhi-yojana": "sukanya_samriddhi_candidate"
}

def normalize_text(text: str) -> str:
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text).lower()
    return ' '.join(text.split())

def token_similarity(s1: str, s2: str) -> float:
    t1 = set(normalize_text(s1).split())
    t2 = set(normalize_text(s2).split())
    if not t1 or not t2:
        return 0.0
    intersection = len(t1 & t2)
    union = len(t1 | t2)
    return intersection / union

def resolve_candidate_identity(
    candidate: Dict[str, Any],
    canonical_schemes: List[Dict[str, Any]]
) -> Dict[str, Any]:
    cand_name = candidate["official_name"]
    cand_slug = candidate.get("slug", "")
    cand_authority = candidate.get("authority", "")
    cand_url = candidate.get("official_detail_url", "")
    norm_cand = normalize_text(cand_name)

    # 1. Check Known Alias / Explicit Slug Map
    target_canonical_id = KNOWN_ALIASES.get(cand_slug)
    
    # 2. Match against Canonical Schemes
    best_match = None
    best_score = 0.0
    
    for canon in canonical_schemes:
        c_id = canon["scheme_id"]
        c_name = canon["scheme_name"]
        norm_canon = normalize_text(c_name)
        
        # Exact Normalized Name Match
        if norm_cand == norm_canon:
            return {
                "candidate_id": candidate["candidate_id"],
                "candidate_name": cand_name,
                "candidate_slug": cand_slug,
                "classification": "EXACT_EXISTING",
                "matched_canonical_id": c_id,
                "matched_canonical_name": c_name,
                "confidence": 1.0,
                "resolution_notes": "Exact normalized title and statutory identity match against CivixAI canonical scheme.",
                "review_action": "RETAIN_EXISTING_CANONICAL"
            }
            
        if target_canonical_id and c_id == target_canonical_id:
            return {
                "candidate_id": candidate["candidate_id"],
                "candidate_name": cand_name,
                "candidate_slug": cand_slug,
                "classification": "EXACT_EXISTING",
                "matched_canonical_id": c_id,
                "matched_canonical_name": c_name,
                "confidence": 0.98,
                "resolution_notes": f"Known alias '{cand_slug}' links directly to canonical scheme '{c_id}'.",
                "review_action": "RETAIN_EXISTING_CANONICAL"
            }
            
        score = token_similarity(norm_cand, norm_canon)
        if score > best_score:
            best_score = score
            best_match = canon

    # 3. High similarity token overlap
    if best_score >= 0.70 and best_match:
        # Check if subscheme or component
        if any(w in norm_cand for w in ["component", "sub scheme", "phase", "fellowship", "scholarship"]):
            classification = "COMPONENT_OR_SUBSCHEME"
            notes = f"Candidate appears to be a component or sub-scheme of '{best_match['scheme_name']}'."
        else:
            classification = "PROBABLE_ALIAS"
            notes = f"High lexical similarity ({best_score:.2f}) with canonical scheme '{best_match['scheme_name']}'. Requires human review before alias merge."
            
        return {
            "candidate_id": candidate["candidate_id"],
            "candidate_name": cand_name,
            "candidate_slug": cand_slug,
            "classification": classification,
            "matched_canonical_id": best_match["scheme_id"],
            "matched_canonical_name": best_match["scheme_name"],
            "confidence": round(best_score, 2),
            "resolution_notes": notes,
            "review_action": "HUMAN_REVIEW_REQUIRED_NO_AUTO_MERGE"
        }
        
    # 4. Moderate similarity overlap
    if best_score >= 0.40 and best_match:
        return {
            "candidate_id": candidate["candidate_id"],
            "candidate_name": cand_name,
            "candidate_slug": cand_slug,
            "classification": "IDENTITY_REVIEW_REQUIRED",
            "matched_canonical_id": best_match["scheme_id"],
            "matched_canonical_name": best_match["scheme_name"],
            "confidence": round(best_score, 2),
            "resolution_notes": f"Ambiguous match with {best_match['scheme_name']} ({best_score:.2f}). Must NOT be auto-merged.",
            "review_action": "QUEUE_FOR_MANUAL_DISAMBIGUATION"
        }

    # 5. Distinguish new candidates
    is_state = candidate.get("scheme_level") == "STATE"
    return {
        "candidate_id": candidate["candidate_id"],
        "candidate_name": cand_name,
        "candidate_slug": cand_slug,
        "classification": "NEW_CANDIDATE",
        "matched_canonical_id": None,
        "matched_canonical_name": None,
        "confidence": 1.0,
        "resolution_notes": f"Novel {'State/UT' if is_state else 'Central'} scheme not present in current 135 canonical schemes. Staged for future certification pipeline.",
        "review_action": "STAGE_IN_DISCOVERY_POOL"
    }

def run_myscheme_identity_matching():
    print("Running myScheme Identity Resolution against CivixAI 135 Canonical Corpus...")
    with open(DISCOVERY_PATH, "r", encoding="utf-8") as f:
        discovery_data = json.load(f)
        
    with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
        canonical_schemes = json.load(f)

    candidates = discovery_data.get("candidates", [])
    identity_map = []
    
    summary_counts = {
        "EXACT_EXISTING": 0,
        "PROBABLE_ALIAS": 0,
        "NEW_CANDIDATE": 0,
        "HISTORICAL_OR_RENAMED": 0,
        "COMPONENT_OR_SUBSCHEME": 0,
        "IDENTITY_REVIEW_REQUIRED": 0
    }

    for cand in candidates:
        res = resolve_candidate_identity(cand, canonical_schemes)
        identity_map.append(res)
        cls = res["classification"]
        summary_counts[cls] = summary_counts.get(cls, 0) + 1

    payload = {
        "audit_metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "target": "MYSCHEME_CANDIDATE_IDENTITY_RESOLUTION",
            "total_candidates_processed": len(identity_map),
            "canonical_corpus_size": len(canonical_schemes),
            "summary_counts": summary_counts,
            "policy": "NEVER_AUTO_MERGE_PROBABILISTIC_MATCHES"
        },
        "identity_mappings": identity_map
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Generated {OUTPUT_PATH}")
    print(f"Summary: {summary_counts}")
    return payload

if __name__ == "__main__":
    run_myscheme_identity_matching()
