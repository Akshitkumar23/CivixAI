import pandas as pd
import re
import os
import time
import requests
import json
from pathlib import Path
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Optional, Dict, Any

# Paths
ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"
MASTER_CSV = DATA_DIR / "master" / "schemes_master.csv"
ENV_PATH = ROOT / ".env"

# Load Env
load_dotenv(ENV_PATH)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Try a few common model names to find one that works for this key
        working_model = None
        for model_name in ['gemini-1.5-flash', 'gemini-pro', 'gemini-1.5-flash-latest']:
            try:
                m = genai.GenerativeModel(model_name)
                m.generate_content("test", request_options={"timeout": 10})
                working_model = model_name
                print(f"Using working model: {working_model}")
                break
            except:
                continue
        
        if working_model:
            model = genai.GenerativeModel(working_model)
        else:
            print("Warning: All Gemini models failed. Falling back to Heuristics.")
            model = None
    except Exception as e:
        print(f"Warning: Gemini config failed: {e}. Falling back to Heuristics.")
        model = None
else:
    print("Warning: GEMINI_API_KEY not found. Falling back to Heuristics.")
    model = None

# ==========================================
# ADVANCED CATEGORY RULES (Fallbacks)
# ==========================================
CATEGORY_RULES = {
    "agriculture": ["kisan", "krishi", "agriculture", "crop", "farmer", "irrigation", "soil", "seed", "horticulture", "agri", "animal husbandry", "dairy", "fishery"],
    "education": ["scholarship", "fellowship", "education", "student", "school", "college", "university", "vidya", "shiksha", "padhai", "academic", "hostel", "internship", "research"],
    "health": ["health", "medical", "swasthya", "arogya", "ayushman", "hospital", "disease", "treatment", "maternity", "medicine", "suraksha", "vaccination", "ayush", "yoga"],
    "housing": ["housing", "awas", "shelter", "ghar", "urban development", "rural housing", "slum"],
    "pension": ["pension", "old age", "widow", "vridha", "vidhwa", "senior citizen", "retirement", "epfo", "social security"],
    "employment": ["employment", "rozgar", "nrega", "job", "shramik", "worker", "labour", "skill", "kaushal", "training", "vocational", "placement"],
    "business": ["business", "loan", "micro", "enterprise", "mudra", "startup", "stand-up", "msme", "udyog", "vyapar", "industry", "entrepreneur", "credit"],
    "women_welfare": ["mahila", "women", "maternity", "pregnant", "girl", "beti", "sukanya", "kanya", "matru", "widow", "mother", "shakti"],
    "child_welfare": ["child", "bal", "infant", "anganwadi", "nutrition", "poshan", "orphan", "kids", "vatsalya"],
    "infrastructure": ["road", "sadak", "gramin", "village", "water", "jal", "electricity", "urja", "telecom", "digital india", "smart city"],
}

# ==========================================
# SMART CRAWLING & AI EXTRACTION
# ==========================================

def fetch_web_content(url: str) -> str:
    """Fetch text content from the URL to help AI understand documents/eligibility."""
    if not url or "gov.in" not in url: return ""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (CivixAI-Enricher/1.0)"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200: return ""
        
        soup = BeautifulSoup(resp.text, 'lxml')
        # Remove scripts, styles
        for s in soup(['script', 'style', 'nav', 'header', 'footer']): s.decompose()
        
        # Get target sections if they exist
        content = ""
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            text = heading.get_text().lower()
            if any(k in text for k in ['document', 'eligibility', 'benefit', 'criteria', 'guideline']):
                content += heading.get_text(separator=' ', strip=True) + "\n"
                nxt = heading.find_next(['p', 'ul', 'ol', 'div'])
                if nxt: content += nxt.get_text(separator=' ', strip=True)[:500] + "\n"
        
        if len(content) < 50: 
             content = soup.get_text(separator=' ', strip=True)[:2000]
             
        return content
    except:
        return ""

def regex_extract_rules(text: str) -> Dict[str, Any]:
    """Smart fallback to extract numeric rules from text using Regex."""
    rules = {"min_age": None, "max_age": None, "income_limit": None, "states": []}
    text_lower = text.lower()
    
    # Extract Age
    age_matches = re.findall(r"(\d{1,2})\s*-\s*(\d{1,2})\s*years", text_lower)
    if age_matches:
        rules["min_age"], rules["max_age"] = age_matches[0]
    else:
        min_age = re.search(r"(?:min|minimum|above|age of)\s*(\d{1,2})", text_lower)
        if min_age: rules["min_age"] = min_age.group(1)
        max_age = re.search(r"(?:max|maximum|below|upto)\s*(\d{1,2})\s*years", text_lower)
        if max_age: rules["max_age"] = max_age.group(1)
        
    # Extract Income (handles Lakhs and raw numbers)
    income = re.search(r"(?:income|income limit|up to|Below)\s*(?:rs\.?|₹)?\s*(\d+(?:,\d+)?(?:\.\d+)?)\s*(lakh|lac)?", text_lower)
    if income:
        val = income.group(1).replace(",", "")
        try:
            num = float(val)
            if income.group(2): # if 'lakh'
                rules["income_limit"] = int(num * 100000)
            else:
                rules["income_limit"] = int(num)
        except: pass
        
    # Extract States (common Indian states)
    common_states = ["haryana", "punjab", "delhi", "maharashtra", "bihar", "rajasthan", "gujarat", "karnataka", "kerala", "tamil nadu", "uttar pradesh", "west bengal", "madhya pradesh"]
    for s in common_states:
        if s in text_lower:
            rules["states"].append(s.title())
            
    return rules

def ai_enrich_scheme(name: str, ministry: str, url: str, current_desc: str) -> Dict[str, str]:
    """Use Gemini AI to extract real documents and granular categories."""
    if not model: return {}
    
    # Optional crawling for context
    web_context = fetch_web_content(url) if url else ""
    
    prompt = f"""
    Analyze this Indian Government Scheme and extract precise eligibility rules:
    Name: {name}
    Ministry: {ministry}
    Context: {web_context[:1500]}
    
    Extract ONLY these fields in valid JSON:
    1. category: (Granular, e.g. 'Tertiary Education Loan')
    2. documents: (Crucial ones, e.g. 'Aadhaar, Caste Cert')
    3. description: (Exact benefits, 2 sentences)
    4. min_age: (integer, keep null if not found)
    5. max_age: (integer, keep null if not found)
    6. income_limit: (integer annual income, keep null if not found)
    7. states: (list of strings, use 'ALL' if central)
    
    Output JSON ONLY:
    {{
        "category": "...",
        "documents": "...",
        "description": "...",
        "min_age": null,
        "max_age": null,
        "income_limit": null,
        "states": []
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"AI Skip for {name}: {e}")
    return {}

def infer_category_fallback(text: str) -> str:
    text = text.lower()
    for cat, keywords in CATEGORY_RULES.items():
        if any(re.search(r'\b' + kw + r'\b', text) for kw in keywords):
            return cat
    return "general_welfare"

def enrich_data():
    if not MASTER_CSV.exists():
        print(f"File not found: {MASTER_CSV}")
        return

    df = pd.read_csv(MASTER_CSV, dtype=str)
    
    # Ensure columns
    cols = ['benefit_description', 'documents_required', 'scheme_category', 'benefit_type', 'min_age', 'max_age', 'income_limit', 'applicable_states']
    for c in cols:
        if c not in df.columns: df[c] = ''

    total = len(df)
    print(f"Starting NLP Rule Extraction & AI enrichment on {total} schemes...")
    
    # Only enrich schemes that look generic or have missing rules
    for i, row in df.iterrows():
        name = str(row.get('scheme_name', ''))
        url = str(row.get('application_url', '')) or str(row.get('source_url', ''))
        ministry = str(row.get('ministry', ''))
        
        # Check if we need rule extraction
        is_missing_rules = pd.isna(row.get('min_age')) or str(row.get('min_age')) == '' or str(row.get('min_age')) == 'nan'
        is_generic = "provides targeted benefits" in str(row['benefit_description']) or "Aadhaar Card, Residence Proof" in str(row['documents_required'])
        
        if is_missing_rules or is_generic:
            print(f"[{i+1}/{total}] Extracting Rules for: {name}")
            ai_data = ai_enrich_scheme(name, ministry, url, str(row['benefit_description']))
            
            if ai_data:
                # ... existing AI save logic ...
                if ai_data.get('category'): df.at[i, 'scheme_category'] = ai_data['category']
                if ai_data.get('documents'): df.at[i, 'documents_required'] = ai_data['documents']
                if ai_data.get('description'): df.at[i, 'benefit_description'] = ai_data['description']
                
                # Rule Extraction
                if ai_data.get('min_age') is not None: df.at[i, 'min_age'] = str(ai_data['min_age'])
                if ai_data.get('max_age') is not None: df.at[i, 'max_age'] = str(ai_data['max_age'])
                if ai_data.get('income_limit') is not None: df.at[i, 'income_limit'] = str(ai_data['income_limit'])
                if ai_data.get('states'): 
                    states_val = ai_data['states']
                    if isinstance(states_val, list):
                        df.at[i, 'applicable_states'] = ", ".join(states_val)
                    else:
                        df.at[i, 'applicable_states'] = str(states_val)
                
                time.sleep(1.2) # Avoid rate limits
            else:
                # Fallback to Regex Rule Extraction (#27)
                print(f"[{i+1}/{total}] Regex-Extracting for: {name}")
                web_context = fetch_web_content(url) if url else ""
                fallback_rules = regex_extract_rules(f"{name} {ministry} {web_context}")
                
                if fallback_rules["min_age"]: df.at[i, 'min_age'] = str(fallback_rules["min_age"])
                if fallback_rules["max_age"]: df.at[i, 'max_age'] = str(fallback_rules["max_age"])
                if fallback_rules["income_limit"]: df.at[i, 'income_limit'] = str(fallback_rules["income_limit"])
                if fallback_rules["states"]: df.at[i, 'applicable_states'] = ", ".join(fallback_rules["states"])
                
                df.at[i, 'scheme_category'] = infer_category_fallback(f"{name} {ministry}")
        
    df.to_csv(MASTER_CSV, index=False)
    print(f"Enrichment Complete. Master file saved.")

if __name__ == "__main__":
    enrich_data()
