import re
from typing import Any, Dict, Optional, Tuple

class BenefitService:
    def __init__(self):
        self.num_pattern = re.compile(r"(\d+(?:,\d+)*(?:\.\d+)?)")

    def estimate_benefit(self, scheme_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses benefit_amount into structured data: amount, unit, frequency.
        Returns: { "amount": float, "is_range": bool, "summary": str }
        """
        raw_val = str(scheme_dict.get("benefit_amount", "")).strip().lower()
        raw_desc = str(scheme_dict.get("benefit_description", "")).strip()

        if raw_val in ["", "nan", "none"]:
            return self._fallback_estimate(raw_desc)

        # Basic range extraction: "₹500 - ₹1000"
        parts = self.num_pattern.findall(raw_val.replace(",", ""))
        if not parts:
            return self._fallback_estimate(raw_desc)

        nums = [float(p) for p in parts]
        
        # Scaling based on "L" (Lakh) or "K"
        scale = 1.0
        if "lakh" in raw_val or " l " in f" {raw_val} " or "l." in raw_val:
            scale = 100000.0
        elif "crore" in raw_val or " cr " in f" {raw_val} " or "cr." in raw_val:
            scale = 10000000.0
        elif "k" in raw_val:
            scale = 1000.0

        if len(nums) >= 2:
            avg = sum(nums) / len(nums)
            return {
                "amount": float(avg * scale),
                "is_range": True,
                "summary": f"₹{int(min(nums)*scale):,} - ₹{int(max(nums)*scale):,}"
            }
        
        return {
            "amount": float(nums[0] * scale),
            "is_range": False,
            "summary": f"₹{int(nums[0]*scale):,}"
        }

    def _fallback_estimate(self, desc: str) -> Dict[str, Any]:
        """
        Heuristic for when amount isn't explicitly defined.
        """
        desc_l = desc.lower()
        if any(k in desc_l for k in ["free", "subsidized", "discount"]):
            return {"amount": 0.0, "is_range": False, "summary": "Services / Kind provided"}
        if any(k in desc_l for k in ["scholarship", "stipend"]):
            return {"amount": 0.0, "is_range": True, "summary": "Scholarship Variable"}
        return {"amount": 0.0, "is_range": False, "summary": "Benefit varies by criteria"}
