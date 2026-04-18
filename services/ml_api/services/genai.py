import os
import random
from typing import Dict, Any, List
import logging
from pathlib import Path
from dotenv import load_dotenv

# Force load the root .env before checking API keys
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent.parent / ".env")

logger = logging.getLogger(__name__)

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


class PersonalizedGenAIService:
    """
    Generates highly personalized, scheme-specific descriptions and reasoning.
    Uses Anthropic Claude or Google Gemini if API keys are provided.
    Falls back to data-driven descriptions if neither is available.
    """

    def __init__(self):
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.llm_provider = None
        
        if self.anthropic_key and HAS_ANTHROPIC:
            self.claude_client = anthropic.Client(api_key=self.anthropic_key)
            self.llm_provider = "anthropic"
            logger.info("REAL GEN-AI INITIALIZED: Connected to Anthropic Claude API.")
        elif self.gemini_key and HAS_GEMINI:
            genai.configure(api_key=self.gemini_key)
            self.gemini_client = genai.GenerativeModel('gemini-1.5-flash-latest')
            self.llm_provider = "gemini"
            logger.info("REAL GEN-AI INITIALIZED: Connected to Google Gemini API.")
        else:
            logger.info("GEN-AI: No API keys found, using data-driven descriptions.")

    def _call_llm(self, prompt: str) -> str:
        """Helper to call whichever LLM is configured."""
        if self.llm_provider == "anthropic":
            response = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=250,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        elif self.llm_provider == "gemini":
            response = self.gemini_client.generate_content(prompt)
            if response.text:
                return response.text.strip()
        return ""

    def _clean_val(self, val: Any, fallback: str = "") -> str:
        """Clean a value, returning fallback if NaN/None/empty."""
        if val is None:
            return fallback
        s = str(val).strip()
        return fallback if s.lower() in ["nan", "none", ""] else s

    def generate_live_description(self, user: Dict[str, Any], scheme: Dict[str, Any], rank_score: float) -> str:
        """
        Generates a UNIQUE, data-driven description for each scheme based on:
        1. The scheme's own benefit_description
        2. The user's specific profile attributes
        3. The scheme's type, ministry, category, benefit amount

        Every scheme gets a DIFFERENT description because it pulls from scheme-specific data.
        """
        # ── Pull actual scheme data ─────────────────────────────────────────
        s_name = self._clean_val(scheme.get("scheme_name"), "this scheme")
        s_desc = self._clean_val(scheme.get("benefit_description"), "")
        s_ministry = self._clean_val(scheme.get("ministry"), "Government of India")
        s_amount = self._clean_val(scheme.get("benefit_amount"), "")
        s_category = self._clean_val(scheme.get("scheme_category"), "welfare").lower()
        s_type = self._clean_val(scheme.get("benefit_type"), "scheme").lower()
        s_level = self._clean_val(scheme.get("scheme_level"), "Central").capitalize()
        docs = self._clean_val(scheme.get("documents_required"), "")
        min_age = self._clean_val(scheme.get("min_age"), "")
        max_age = self._clean_val(scheme.get("max_age"), "")
        income_limit = self._clean_val(scheme.get("income_limit"), "")

        # ── Pull user profile ───────────────────────────────────────────────
        user_occ = self._clean_val(user.get("occupation"), "citizen").capitalize()
        user_age = self._clean_val(user.get("age"), "")
        user_state = self._clean_val(user.get("state"), "India").capitalize()
        user_gender = self._clean_val(user.get("gender"), "").lower()
        user_income = user.get("annual_income") or user.get("annualIncome") or 0
        user_caste = self._clean_val(user.get("caste") or user.get("category"), "").upper()

        # ── Try REAL GEN-AI first ───────────────────────────────────────────
        if self.llm_provider and s_desc:
            try:
                prompt = (
                    f"Write a 2-3 sentence personalized recommendation for a {user_age}-year-old {user_occ} "
                    f"from {user_state} (income: Rs.{user_income}/year) who qualifies for '{s_name}'. "
                    f"Key benefit: {s_desc[:200]}. Be specific, enthusiastic, under 40 words. "
                    f"Start with 'You qualify for...' or 'As a {user_occ}...'. Don't repeat generic phrases."
                )
                response_text = self._call_llm(prompt)
                if response_text:
                    return response_text.replace("\n", " ")
            except Exception as e:
                logger.error(f"GenAI Failed, using data-driven fallback: {e}")

        # ── DATA-DRIVEN FALLBACK: Build unique desc from scheme's own data ──
        # Use the actual benefit description if available (most unique source)
        if s_desc and len(s_desc) > 30:
            # Trim and personalize the actual scheme description
            short_desc = s_desc[:180].rstrip(".,") + "."

            # Add user-specific matching note
            match_note = ""
            if user_income and income_limit:
                try:
                    if float(user_income) <= float(income_limit):
                        match_note = f" Your income of ₹{int(float(user_income)):,} fits within the eligibility limit."
                except (ValueError, TypeError):
                    pass

            gender_note = ""
            if user_gender == "female" and any(k in s_name.lower() for k in ["mahila", "stree", "beti", "women", "nari"]):
                gender_note = " Specifically designed for women like you."

            caste_note = ""
            if user_caste in ["SC", "ST", "OBC"] and any(k in (s_name + s_desc).lower() for k in ["sc", "st", "obc", "scheduled", "tribal", "backward"]):
                caste_note = f" Prioritized for {user_caste} beneficiaries."

            conf_note = ""
            if rank_score > 0.8:
                conf_note = " ⭐ Rated Top Match by our AI engine."
            elif rank_score > 0.6:
                conf_note = " Highly recommended for your profile."

            return f"{short_desc}{match_note}{gender_note}{caste_note}{conf_note}".strip()

        # ── LAST RESORT: Structured description using scheme metadata ───────
        parts: List[str] = []

        # Opening based on scheme type
        if s_type == "loan":
            parts.append(f"{s_name} provides financial credit support through {s_ministry}.")
        elif s_type == "insurance":
            parts.append(f"{s_name} offers insurance/protection coverage managed by {s_ministry}.")
        elif "education" in s_category or "scholarship" in s_category:
            parts.append(f"{s_name} is an educational support initiative under {s_ministry}.")
        elif "agriculture" in s_category or "farmer" in s_category:
            parts.append(f"{s_name} is a farmer-focused scheme by {s_ministry}.")
        elif "health" in s_category:
            parts.append(f"{s_name} provides healthcare coverage under {s_ministry}.")
        else:
            parts.append(f"{s_name} is a {s_level} Government scheme under {s_ministry}.")

        # Benefit amount if available
        if s_amount:
            parts.append(f"Provides up to {s_amount} in benefits.")

        # Age eligibility
        if min_age and max_age:
            try:
                parts.append(f"Open to applicants aged {int(float(min_age))}–{int(float(max_age))} years.")
            except (ValueError, TypeError):
                pass

        # User match note
        if user_occ and user_occ.lower() != "citizen":
            parts.append(f"Matched with you as a {user_occ} from {user_state}.")
        else:
            parts.append(f"Eligible for residents of {user_state}.")

        return " ".join(parts)

    def generate_tldr(self, scheme: Dict[str, Any]) -> list:
        """Generates 3 actionable bullet points for the Scheme Details page."""
        s_name = self._clean_val(scheme.get("scheme_name"), "this scheme")
        b_amt = self._clean_val(scheme.get("benefit_amount"), "")
        processing = self._clean_val(scheme.get("processing_time"), "15-30 days")
        s_type = self._clean_val(scheme.get("benefit_type"), "scheme").lower()

        bullets = []
        if b_amt:
            bullets.append({"icon": "💰", "title": "Benefit Value", "text": f"Provides up to {b_amt} in direct assistance."})
        elif s_type == "loan":
            bullets.append({"icon": "🏦", "title": "Credit Support", "text": "Offers subsidized loan/credit facility through partner banks."})
        elif s_type == "insurance":
            bullets.append({"icon": "🛡️", "title": "Coverage", "text": "Provides insurance coverage for life or health emergencies."})
        else:
            bullets.append({"icon": "🎯", "title": "Primary Support", "text": "Offers targeted resources and direct government support."})

        bullets.append({"icon": "⏱️", "title": "Processing Time", "text": f"Estimated processing time is around {processing}."})

        cat = self._clean_val(scheme.get("scheme_category"), "").lower()
        if "education" in cat or "scholarship" in cat:
            bullets.append({"icon": "📚", "title": "For Students", "text": "Designed for students pursuing higher or basic education."})
        elif "agriculture" in cat or "farmer" in cat:
            bullets.append({"icon": "🌾", "title": "For Farmers", "text": "Aimed specifically at farmers and agricultural workers."})
        elif "health" in cat:
            bullets.append({"icon": "🏥", "title": "Healthcare", "text": "Covers medical expenses and health-related support."})
        elif s_type == "loan":
            bullets.append({"icon": "💼", "title": "Business/Finance", "text": "Supports entrepreneurs and small business owners with credit access."})
        else:
            bullets.append({"icon": "🏛️", "title": "Governance", "text": "Managed continuously by the relevant Government Ministry."})

        return bullets

    def generate_application_steps(self, scheme: Dict[str, Any]) -> list:
        """Generates 'How To Apply' steps based on scheme category and data."""
        s_name = self._clean_val(scheme.get("scheme_name"), "this scheme")
        cat = self._clean_val(scheme.get("scheme_category"), "").lower()
        ministry = self._clean_val(scheme.get("ministry"), "the government portal")
        s_type = self._clean_val(scheme.get("benefit_type"), "scheme").lower()
        raw_process = self._clean_val(scheme.get("application_process"), "")

        if raw_process and len(raw_process) > 30 and self.llm_provider:
            try:
                import json
                prompt = (
                    f"Read this raw application process for '{s_name}': '{raw_process[:500]}'. "
                    "Extract exactly 3 concise steps on how to apply. Return strictly as a valid JSON array: "
                    "[{\"step\": 1, \"title\": \"...\", \"description\": \"...\"}]"
                )
                json_str = self._call_llm(prompt)
                if json_str.startswith("```json"):
                    json_str = json_str.split("```json")[-1].split("```")[0].strip()
                elif json_str.startswith("```"):
                    json_str = json_str.split("```")[-1].split("```")[0].strip()
                steps = json.loads(json_str)
                if isinstance(steps, list) and len(steps) >= 1 and "title" in steps[0]:
                    return steps[:3]
            except Exception as e:
                logger.error(f"GenAI steps failed, using fallback. Error: {e}")

        if s_type == "loan" or "loan" in cat or "business" in cat:
            return [
                {"step": 1, "title": "Prepare Documents", "description": "Gather your Aadhaar, PAN, income proof, and business plan."},
                {"step": 2, "title": "Apply at Bank/Portal", "description": f"Visit the nearest bank or apply online through {ministry}'s official portal."},
                {"step": 3, "title": "Branch Verification", "description": "Visit the bank branch for KYC verification and loan sanction."}
            ]
        elif s_type == "insurance" or "health" in cat or "insurance" in cat:
            return [
                {"step": 1, "title": "Check Eligibility", "description": "Search your name in the official beneficiary database using Aadhaar."},
                {"step": 2, "title": "Visit CSC or Hospital", "description": "Go to the nearest Common Service Center or empanelled hospital."},
                {"step": 3, "title": "Get e-Card/Policy", "description": "Provide your Aadhaar to generate your digital insurance/health card."}
            ]
        elif "education" in cat or "scholarship" in cat:
            return [
                {"step": 1, "title": "Gather Academic Docs", "description": "Ensure your marksheet, fee receipts, and category certificate are ready."},
                {"step": 2, "title": "Apply on NSP Portal", "description": f"Register online on the National Scholarship Portal (NSP) under {ministry}."},
                {"step": 3, "title": "Institute Verification", "description": "Your school/college nodal officer will digitally verify your application."}
            ]
        elif "agriculture" in cat or "farmer" in cat:
            return [
                {"step": 1, "title": "Register at Patwari/Agriculture Office", "description": "Visit the local Patwari or Agriculture Department with land records."},
                {"step": 2, "title": "eKYC with Aadhaar", "description": "Complete biometric Aadhaar eKYC at the nearest Common Service Centre."},
                {"step": 3, "title": "DBT Transfer Confirmation", "description": "Link your Aadhaar to your bank account. Amount will be transferred via DBT."}
            ]
        else:
            return [
                {"step": 1, "title": "Gather Documents", "description": "Collect your Aadhaar, income certificate, residence proof, and category certificate."},
                {"step": 2, "title": "Online Application", "description": f"Navigate to the official portal for {ministry} and submit your details online."},
                {"step": 3, "title": "Track & Receive", "description": "Track your application ID. Benefits will be routed securely via DBT to your linked bank account."}
            ]

    def generate_short_reasoning(self, user: Dict[str, Any], scheme: Dict[str, Any]) -> str:
        s_cat = self._clean_val(scheme.get("scheme_category"), "welfare").capitalize()
        user_occ = self._clean_val(user.get("occupation"), "citizen").capitalize()
        reasons = [
            f"AI matched your {user_occ} profile with {s_cat} requirements.",
            f"High affinity between {user_occ} needs and {s_cat} scheme goals.",
            f"Your {user_occ} status qualifies for this {s_cat} benefit.",
            f"Contextual match: Being a {user_occ} makes you an ideal {s_cat} beneficiary.",
        ]
        return random.choice(reasons)
