import pandas as pd
df = pd.read_csv('data/master/schemes_master.csv')
print("Total valid scheme names:", df['scheme_name'].notna().sum())
print("First 30 scheme names:")
count = 0
for name in df['scheme_name'].dropna():
    if count >= 30: break
    print(f"{count}: {str(name)[:100]}")
    count+=1
