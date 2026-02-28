import sys
from pathlib import Path
import joblib  # type: ignore

# Add services/ml to sys.path
ml_dir = Path(__file__).resolve().parent / "services" / "ml"
if str(ml_dir) not in sys.path:
    sys.path.append(str(ml_dir))

models_dir = ml_dir / "models"

try:
    print("Loading eligibility model...")
    elig_model = joblib.load(models_dir / "eligibility_model.pkl")
    print("Eligibility model loaded successfully.")
    
    print("Loading benefit model...")
    ben_model = joblib.load(models_dir / "benefit_model.pkl")
    print("Benefit model loaded successfully.")
except Exception as e:
    print(f"Error loading models: {e}")
    import traceback
    traceback.print_exc()
