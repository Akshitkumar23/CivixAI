"""
CivixAI Live India.gov.in Coverage Snapshot Connector
Refreshes the live coverage snapshot from official India.gov.in portals.
Stores source URL, timestamp, reported count, definition, and deduplication/currentness caveats.
Generates data/live_india_gov_coverage_snapshot.json.
"""
import urllib.request
import ssl
import re
import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "live_india_gov_coverage_snapshot.json"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def run_india_gov_snapshot():
    print("Refreshing India.gov.in Live Coverage Snapshot...")
    url = "https://www.india.gov.in/my-government/schemes"
    homepage_url = "https://www.india.gov.in"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    retrieved_at = datetime.now(timezone.utc).isoformat()
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=20) as res:
            http_status = res.status
            html = res.read().decode('utf-8', errors='ignore')
            fetch_success = True
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        http_status = 500
        html = ""
        fetch_success = False

    # Also query homepage to inspect exposed portal service / scheme metrics
    try:
        req_hp = urllib.request.Request(homepage_url, headers=headers)
        with urllib.request.urlopen(req_hp, context=ctx, timeout=20) as res_hp:
            html_hp = res_hp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        html_hp = ""

    # Parse potential counts / metrics
    hp_metrics = re.findall(r'(\d+[\d,]*)\s*(?:Services|Schemes|Forms|Citizen Services)', html_hp, re.I)

    # India.gov.in official definitions and caveats
    report = {
        "snapshot_metadata": {
            "source_authority": "National Informatics Centre (NIC) / Ministry of Electronics and Information Technology (MeitY)",
            "primary_source_url": url,
            "homepage_url": homepage_url,
            "retrieved_at": retrieved_at,
            "http_status": http_status,
            "fetch_success": fetch_success,
            "content_length_bytes": len(html)
        },
        "live_coverage_data": {
            "reported_scope_indicator": "Federated National Scheme & Citizen Service Directory",
            "homepage_exposed_metrics": hp_metrics,
            "direct_portal_links": {
                "myscheme_integration": "https://www.myscheme.gov.in (Embedded National Scheme Partner)",
                "schemes_directory": "https://www.india.gov.in/my-government/schemes",
                "national_portal_services": "https://services.india.gov.in"
            }
        },
        "programme_definition_and_scope_caveats": {
            "definition": (
                "India.gov.in functions as a federated directory indexing Central and State statutory welfare programmes, "
                "citizen public services, institutional grants, and administrative circulars."
            ),
            "scope_caveats": [
                "1. Administrative Overlap: Entries combine statutory entitlement schemes, temporary relief packages, and departmental public service forms.",
                "2. Federated Duplication: Central sector schemes implemented through states often appear under both Central Ministry and State Department headings.",
                "3. Currentness Decay: Historical or subsumed programmes remain discoverable for informational and administrative tracking.",
                "4. Non-Additivity: India.gov.in catalog counts CANNOT be equated directly with unique active citizen entitlement programs without legal deduplication."
            ],
            "deduplication_policy": (
                "CivixAI stages India.gov.in listings as SchemeDiscoveryCandidate records in the DISCOVERY_POOL. "
                "No India.gov.in record is granted legal eligibility status until verified against statutory guidelines."
            )
        }
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Generated {OUTPUT_PATH}")
    print(f"India.gov Status: {http_status}, Metrics: {hp_metrics}")

if __name__ == "__main__":
    run_india_gov_snapshot()
