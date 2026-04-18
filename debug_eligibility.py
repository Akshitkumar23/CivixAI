import sys
sys.path.insert(0, ".")
import pandas as pd
from services.ml_api.services.eligibility import EligibilityService

class UserProfile:
    def __init__(self):
        self.age = 60
        self.annualIncome = 0
        self.state = "Uttar Pradesh"
        self.caste = "obc"
        self.occupation = "farmer"
        self.hasLand = False
        self.gender = "male"

schemes = pd.read_csv("data/master/schemes_master.csv")
es = EligibilityService(None, {})
u = UserProfile()

eligible_count = 0
reasons_dist = {}

for _, r in schemes.iterrows():
    res = es._rule_based_explain(u, r.to_dict())
    if res["eligible_rules"]:
        eligible_count += 1
    else:
        reason_str = str(res["reasons"])
        reasons_dist[reason_str] = reasons_dist.get(reason_str, 0) + 1

print(f"Eligible Count: {eligible_count}")
for r, count in sorted(reasons_dist.items(), key=lambda x: -x[1])[:10]:
    print(f"{count}x: {r}")
