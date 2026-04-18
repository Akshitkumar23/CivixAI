import pandas as pd
import sys
from pathlib import Path

# Add services to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent / "services" / "ml_api"))
sys.path.append(str(Path(__file__).resolve().parent.parent / "services" / "ml_api" / "services"))

from services.eligibility import EligibilityService
from services.ranking import RankingService
from services.benefit import BenefitService

class MockUser:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.age = kwargs.get('age')
        self.annualIncome = kwargs.get('annualIncome')
        self.state = kwargs.get('state')
        self.caste = kwargs.get('caste')
        self.occupation = kwargs.get('occupation')
        self.gender = kwargs.get('gender')
        self.hasLand = kwargs.get('hasLand', False)

def internal_check():
    # 1. LOAD DATA
    csv_path = Path(__file__).resolve().parent.parent / "data" / "master" / "schemes_master.csv"
    df = pd.read_csv(csv_path)
    
    # 2. INIT SERVICES
    el_service = EligibilityService(None, {})
    rank_service = RankingService()
    ben_service = BenefitService()

    # 3. PROFILES
    u1 = MockUser(age=21, annualIncome=120000, state="Maharashtra", caste="SC", occupation="student", gender="male")
    u2 = MockUser(age=48, annualIncome=300000, state="Uttar Pradesh", caste="General", occupation="farmer", gender="male", hasLand=True)

    print(f"--- INTERNAL AI ENGINE CHECK ---")
    print(f"Testing across {len(df)} schemes...\n")

    for u, label in [(u1, "Student (SC, 1.2L, Maha)"), (u2, "Farmer (Gen, 3L, UP)")]:
        results = []
        for _, row in df.iterrows():
            scheme = row.to_dict()
            el_res = el_service.check_eligibility(u, scheme, 0.9) # Mock high probability
            if not el_res.is_eligible: continue
            
            score = rank_service.score_scheme(u, scheme, el_res, 0.8) # Mock Benefit
            results.append({"name": scheme['scheme_name'], "score": score, "reasons": el_res.reasons})
        
        results.sort(key=lambda x: x['score'], reverse=True)
        print(f"[{label}] TOP 3 MATCHES:")
        for r in results[:3]:
            print(f"- {r['name']} (Rank Score: {r['score']:.2f})")
            print(f"  Reason: {r['reasons'][0]}")
        print("-" * 30)

if __name__ == "__main__":
    internal_check()
