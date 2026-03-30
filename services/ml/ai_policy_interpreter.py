import google.generativeai as genai
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Setup paths
ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = ROOT / "data" / "master" / "policy_directives.json"

def interpret_and_apply(directive_text: str):
    print(f"--- AI Semantic Strategic Interpreter ---")
    print(f"Directive Input: '{directive_text}'")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY NOT FOUND. Cannot perform AI interpretation.")
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

    prompt = f"""
    Analyze the following Government Policy Directive. 
    Extract the key keywords/tags, target locations (states), target categories, and a boost factor (1.0 - 5.0).
    Target only schemes related to the intent.

    Directive: "{directive_text}"

    Respond ONLY with JSON in this structure:
    {{
       "keywords": ["tag1", "tag2"],
       "target_states": ["state1", "all"],
       "target_categories": ["category1", "any"],
       "boost_factor": 2.5,
       "description": "Short internal summary",
       "expiry_days": 7
    }}
    """

    try:
        # Try a few common model strings
        working_model = None
        for m_name in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']:
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content(prompt, request_options={"timeout": 15})
                working_model = m_name
                break
            except: continue
        
        if working_model:
            # Parse result
            raw_text = response.text.strip()
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            directive_data = json.loads(raw_text)
        else:
            raise Exception("No Gemini models reachable")

    except Exception as e:
        print(f"AI Model failed, using Heuristic Fallback for: {directive_text}")
        # Rule-based fallback
        text = directive_text.lower()
        directive_data = {
            "keywords": [w for w in ["women", "business", "msme", "solar", "ev", "pollute", "agri", "student", "scholar", "seed", "loan", "farmer"] if w in text],
            "target_states": [s for s in ["maharashtra", "delhi", "punjab", "haryana", "bihar", "gujarat", "karnataka", "tamil nadu", "kerala", "west bengal", "uttar pradesh", "madhya pradesh"] if s in text],
            "target_categories": ["any"],
            "boost_factor": 3.0 if "3x" in text or "triple" in text else 2.0 if "2x" in text or "boost" in text or "promote" in text else 1.5,
            "description": f"Heuristic match for: {directive_text}",
            "expiry_days": 7
        }
        if not directive_data["target_states"]: directive_data["target_states"] = ["all"]

    print(f"Directive Success: {directive_data['description']}")
    
    # Load existing config
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            try:
                config = json.load(f)
            except: config = {"active_directives": []}
    else:
        config = {"active_directives": []}
        
    config["active_directives"].append(directive_data)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
        
    print(f"✅ Strategic Directive Active in policy_directives.json")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
    else:
        command = input("Enter Policy Directive (e.g. 'Boost EV schemes for Delhi'): ")
    
    interpret_and_apply(command)
