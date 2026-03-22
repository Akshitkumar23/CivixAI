import pandas as pd
from pathlib import Path

MASTER_PATH = Path(r'data/master/schemes_master.csv')

def audit():
    df = pd.read_csv(MASTER_PATH, dtype=str)
    print(f"Total Schemes: {len(df)}")
    print(f"Empty/Nan Apps: {df['application_url'].isna().sum() + (df['application_url'] == 'nan').sum()}")
    print("\nSample Links:")
    print(df[['scheme_name', 'application_url']].head(20))

if __name__ == "__main__":
    audit()
