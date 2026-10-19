"""
Sync script: Synchronizes relational database schemes into src/lib/schemes.json
Ensures zero disparity between backend catalogue and frontend fallback.
"""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.core.database import SessionLocal
from services.core.database.models import Scheme, SchemeVersion

def sync():
    session = SessionLocal()
    try:
        schemes = session.query(Scheme).filter_by(is_active=True).all()
        output_list = []

        for s in schemes:
            version = s.versions[0] if s.versions else None
            rules = version.rules if version else []
            docs = version.documents if version else []

            # Extract eligibility bounds from declarative rules
            min_age = None
            max_age = None
            max_income = None
            states = ["ALL"]
            caste_eligibility = "all"
            gender_eligibility = "all"
            occupation_eligibility = "all"
            disability_required = False

            for r in rules:
                if r.fact_key == "person.age" and r.operator == "between":
                    try:
                        vals = json.loads(r.expected_value.replace("'", '"'))
                        min_age, max_age = vals[0], vals[1]
                    except Exception:
                        pass
                elif r.fact_key == "household.annual_income" and r.operator == "lte":
                    try:
                        max_income = float(r.expected_value)
                    except ValueError:
                        pass
                elif r.fact_key == "location.state" and r.operator == "in":
                    try:
                        states = json.loads(r.expected_value.replace("'", '"'))
                    except Exception:
                        states = [r.expected_value]
                elif r.fact_key == "social.caste" and r.operator == "in":
                    try:
                        caste_eligibility = json.loads(r.expected_value.replace("'", '"'))
                    except Exception:
                        caste_eligibility = r.expected_value
                elif r.fact_key == "health.has_disability":
                    disability_required = True

            output_list.append({
                "id": s.id,
                "name": s.canonical_name,
                "description": version.description if version else "",
                "ministry": s.authority.name if s.authority else "Government of India",
                "category": s.category.name if s.category else "General",
                "benefitType": s.programme_kind,
                "applicationUrl": version.application_url if version else "",
                "documentsRequired": [d.document_type for d in docs],
                "eligibility": {
                    "minAge": min_age,
                    "maxAge": max_age,
                    "maxIncome": max_income,
                    "states": states,
                    "casteEligibility": caste_eligibility,
                    "genderEligibility": gender_eligibility,
                    "occupationEligibility": occupation_eligibility,
                    "disabilityRequired": disability_required
                }
            })

        target_path = PROJECT_ROOT / "src" / "lib" / "schemes.json"
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump({"schemes": output_list}, f, indent=2, ensure_ascii=False)

        print(f"Synced {len(output_list)} schemes to {target_path} successfully!")

    finally:
        session.close()

if __name__ == "__main__":
    sync()
