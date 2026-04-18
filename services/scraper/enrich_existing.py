import pandas as pd
import time
import sys
from pathlib import Path

# Add the scraper directory to sys.path to import from scrape_schemes
SCRAPER_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRAPER_DIR))

from scrape_schemes import fetch_deep_details, load_sources, MASTER_PATH, MASTER_COLUMNS

def enrich_existing_schemes():
    """
    Loads the existing master CSV and runs 'Deep Extraction' on rows
    that are missing application process or detailed documents.
    """
    if not MASTER_PATH.exists():
        print(f"Error: Master CSV not found at {MASTER_PATH}")
        return

    print(f"Loading existing schemes from {MASTER_PATH}...")
    df = pd.read_csv(MASTER_PATH)
    
    # Shuffle to distribute load across different host domains
    df = df.sample(frac=1.0).reset_index(drop=True)
    
    # Ensure new columns exist
    if "application_process" not in df.columns:
        df["application_process"] = ""
    
    user_agent, rate_limit, _ = load_sources()
    
    # Identify rows that need enrichment (missing process or very short descriptions)
    mask = (
        (df["application_process"].isna()) | 
        (df["application_process"] == "") | 
        (df["documents_required"].isna()) |
        (df["documents_required"] == "")
    )
    
    enrich_count = mask.sum()
    print(f"Found {enrich_count} schemes needing deep enrichment.")
    
    if enrich_count == 0:
        print("Everything is already up to date!")
        return

    count = 0
    for idx, row in df[mask].iterrows():
        url = str(row.get("application_url", "") or row.get("source_url", "")).strip()
        if not url or url.lower() == "nan" or not url.startswith("http"):
            continue
            
        print(f"[{count+1}/{enrich_count}] Deep Extracting: {row['scheme_name']}...")
        
        try:
            details = fetch_deep_details(url, user_agent)
            
            if details:
                # Update specific fields if found
                if details.get("application_process"):
                    df.at[idx, "application_process"] = details["application_process"]
                    
                if details.get("documents_required") and (pd.isna(row["documents_required"]) or row["documents_required"] == ""):
                    df.at[idx, "documents_required"] = details["documents_required"]
                
                if details.get("benefit_description") and (pd.isna(row["benefit_description"]) or len(str(row["benefit_description"])) < 100):
                    df.at[idx, "benefit_description"] = details["benefit_description"]
                    
                if details.get("min_age") and (pd.isna(row["min_age"]) or str(row["min_age"]) == ""):
                     df.at[idx, "min_age"] = details["min_age"]

                if details.get("max_age") and (pd.isna(row["max_age"]) or str(row["max_age"]) == ""):
                     df.at[idx, "max_age"] = details["max_age"]

            count += 1
            time.sleep(rate_limit) 
            
            # BATCH COOL-DOWN: Every 10 successes, take a longer break
            if count % 10 == 0:
                print("--- Batch cool-down per user request (5s) ---")
                time.sleep(5)
                df.to_csv(MASTER_PATH, index=False, encoding="utf-8")
                
        except Exception as e:
            print(f"Failed to enrich {row['scheme_name']}: {e}")

    # Final Save
    df.to_csv(MASTER_PATH, index=False, encoding="utf-8")
    print(f"Successfully enriched {count} schemes with Real-World logic.")

if __name__ == "__main__":
    enrich_existing_schemes()
