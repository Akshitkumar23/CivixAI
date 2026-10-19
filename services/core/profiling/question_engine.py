from typing import Any, Dict, List, Optional
from services.core.facts.registry import FACT_CATALOGUE

# Human-friendly question templates for each fact key
QUESTION_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "person.age": {
        "title": "What is your current age?",
        "subtitle": "Age determines eligibility for youth, student, and senior citizen benefits.",
        "input_type": "number",
        "placeholder": "e.g. 25"
    },
    "location.state": {
        "title": "Which State or Union Territory do you reside in?",
        "subtitle": "Many welfare programmes are state-specific or have state-level quotas.",
        "input_type": "select",
        "options": [
            "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa",
            "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
            "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
            "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
            "Uttar Pradesh", "Uttarakhand", "West Bengal", "Delhi", "Jammu and Kashmir"
        ]
    },
    "household.annual_income": {
        "title": "What is your approximate annual household income?",
        "subtitle": "Many welfare schemes have family income caps to ensure assistance reaches eligible households.",
        "input_type": "number",
        "placeholder": "e.g. 150000"
    },
    "occupation.type": {
        "title": "What is your primary occupation or current life situation?",
        "subtitle": "Directs you to targeted schemes for farmers, students, workers, or business owners.",
        "input_type": "select",
        "options": [
            {"label": "Farmer / Cultivator", "value": "farmer"},
            {"label": "Student / Learner", "value": "student"},
            {"label": "Employed (Salaried)", "value": "employed"},
            {"label": "Self-Employed / Business", "value": "self_employed"},
            {"label": "Daily Wage Worker / Labourer", "value": "daily_wage"},
            {"label": "Artisan / Craftsman", "value": "artisan"},
            {"label": "Unemployed", "value": "unemployed"},
            {"label": "Retired / Senior", "value": "retired"}
        ]
    },
    "social.caste": {
        "title": "Do you wish to check category-specific affirmative schemes?",
        "subtitle": "Some central and state programmes have dedicated allocations for SC, ST, OBC, or Minority communities.",
        "input_type": "select",
        "options": [
            {"label": "General", "value": "general"},
            {"label": "OBC (Other Backward Class)", "value": "obc"},
            {"label": "SC (Scheduled Caste)", "value": "sc"},
            {"label": "ST (Scheduled Tribe)", "value": "st"},
            {"label": "Prefer not to say / Skip", "value": "general"}
        ]
    },
    "health.has_disability": {
        "title": "Do you or any family member have a benchmark disability (>=40%)?",
        "subtitle": "Required to unlock specialized Divyangjan welfare and assistive device grants.",
        "input_type": "boolean",
        "options": [
            {"label": "Yes", "value": True},
            {"label": "No", "value": False}
        ]
    },
    "agriculture.has_land": {
        "title": "Do you own cultivable agricultural land?",
        "subtitle": "Key requirement for agricultural subsidies and direct income transfer like PM-Kisan.",
        "input_type": "boolean",
        "options": [
            {"label": "Yes", "value": True},
            {"label": "No", "value": False}
        ]
    },
    "social.is_bpl": {
        "title": "Does your household hold a Below Poverty Line (BPL) or Antyodaya ration card?",
        "subtitle": "Unlocks food security and free housing subsidies.",
        "input_type": "boolean",
        "options": [
            {"label": "Yes", "value": True},
            {"label": "No", "value": False}
        ]
    }
}

class QuestionEngine:
    """
    Adaptive Next-Best-Question selector.
    Calculates information gain on unresolved rule facts.
    """
    def get_next_question(
        self,
        current_facts: Dict[str, Any],
        needs_info_schemes: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        # 1. Count unresolved fact frequencies across candidate schemes
        missing_fact_counts: Dict[str, int] = {}
        for s in needs_info_schemes:
            for f in s.get("missing_facts", []):
                if f not in current_facts:
                    missing_fact_counts[f] = missing_fact_counts.get(f, 0) + 1

        if not missing_fact_counts:
            # Check high-impact core facts if missing
            core_priority = ["location.state", "person.age", "occupation.type", "household.annual_income"]
            for cp in core_priority:
                if cp not in current_facts:
                    template = QUESTION_TEMPLATES.get(cp)
                    if template:
                        return {
                            "fact_key": cp,
                            "impact_count": len(needs_info_schemes),
                            **template
                        }
            return None

        # 2. Pick fact key with highest impact
        sorted_facts = sorted(missing_fact_counts.items(), key=lambda x: x[1], reverse=True)
        top_fact, impact_count = sorted_facts[0]

        template = QUESTION_TEMPLATES.get(top_fact, {
            "title": f"Please provide your {top_fact.replace('.', ' ').title()}",
            "subtitle": "Helps clarify eligibility for pending programmes.",
            "input_type": "text",
            "placeholder": "Enter value"
        })

        return {
            "fact_key": top_fact,
            "impact_count": impact_count,
            **template
        }
