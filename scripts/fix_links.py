import pandas as pd
import numpy as np
from pathlib import Path

MASTER_PATH = Path(r'c:\Users\akshi\Desktop\CivixAI\data\master\schemes_master.csv')

def fix_links():
    if not MASTER_PATH.exists():
        print("CSV not found.")
        return

    df = pd.read_csv(MASTER_PATH, dtype=str)
    count = 0

    def resolve_url(url, name, category):
        # Convert to string and handle nan
        url_str = str(url).strip().lower() if pd.notna(url) else ""
        name = str(name or "").lower()
        cat = str(category or "").lower()

        # Check if it was essentially a broken link or empty
        generic_patterns = ["dbtbharat.gov.in/central-scheme/list", "pmjay.gov.in", "pmaymis.gov.in"]
        is_broken = any(p in url_str for p in generic_patterns) or url_str == "" or url_str == "nan"

        if is_broken:
            # Smart Resolving
            if "scholarship" in name: return "https://scholarships.gov.in/"
            if "loan" in name or "mudra" in name or "credit" in name: return "https://www.jansamarth.in"
            if "kisan" in name or "farmer" in name: return "https://pmkisan.gov.in/"
            if "awas" in name or "housing" in name: return "https://pmay-urban.gov.in/pma-online-application"
            if "ayushman" in name or "pm-jay" in name: return "https://beneficiary.nha.gov.in/"
            if "pension" in name: return "https://enps.nsdl.com/"
            
            # Category Fallbacks
            if cat == "education": return "https://scholarships.gov.in/"
            if cat == "agriculture": return "https://pmkisan.gov.in/"
            if "yojana" in name or "scheme" in name or "mission" in name:
                 return "https://www.india.gov.in/my-government/schemes"
                 
            return "https://www.india.gov.in/my-government/schemes"
        
        return url

    # Apply fix
    for idx, row in df.iterrows():
        old_url = row['application_url']
        new_url = resolve_url(old_url, row['scheme_name'], row['scheme_category'])
        
        if str(old_url) != str(new_url):
            df.at[idx, 'application_url'] = new_url
            count += 1

    df.to_csv(MASTER_PATH, index=False, encoding='utf-8')
    print(f"✅ Aggressively fixed {count} links (including remaining 80 nans).")

if __name__ == "__main__":
    fix_links()
