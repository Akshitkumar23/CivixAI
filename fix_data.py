import pandas as pd
import numpy as np

# Load the dataset
csv_path = 'data/master/schemes_master.csv'
df = pd.read_csv(csv_path)

print(f"Total schemes initially: {len(df)}")

# 1. Fix 'benefit_type' for loans and insurances
# If benefit_type is missing or 'scheme', try to detect 'loan' or 'insurance'
def detect_type(row):
    combined_text = str(row.get('scheme_name', '')).lower() + " " + str(row.get('benefit_description', '')).lower()
    if pd.isna(row.get('benefit_type')) or row.get('benefit_type') == 'scheme' or row.get('benefit_type') == 'central':
        if any(kw in combined_text for kw in ["loan", "credit", "mudra", "interest subvention", "rin", "kcc"]):
            return "loan"
        elif any(kw in combined_text for kw in ["insurance", "bima", "pension", "suraksha", "vay vandana", "mandhan", "life cover"]):
            return "insurance"
    return row.get('benefit_type', 'scheme')

if 'benefit_type' not in df.columns:
    df['benefit_type'] = 'scheme'

df['benefit_type'] = df.apply(detect_type, axis=1)

print("Benefit Types distribution after fix:")
print(df['benefit_type'].value_counts())

# 2. Fix URLs
# Many URLs might just be 'https://myscheme.gov.in' or 'https://india.gov.in'
# We can enhance them to be search URLs if they are too generic.
import urllib.parse

def improve_url(row):
    url = str(row.get('application_url', ''))
    source = str(row.get('source_url', ''))
    
    # Use source if application_url is missing
    if url == 'nan' or url == '' or pd.isna(url):
        url = source if source != 'nan' and not pd.isna(source) else ''
        
    generic_domains = ['myscheme.gov.in', 'india.gov.in', 'pmkisan.gov.in']
    
    # If the URL is very short or is just a generic domain without path
    if url and any(domain in url for domain in generic_domains):
        # Check if it's literally just the homepage (e.g., https://www.myscheme.gov.in/ or https://www.myscheme.gov.in)
        if url.strip('/') in [f"https://www.{d}" for d in generic_domains] or \
           url.strip('/') in [f"http://www.{d}" for d in generic_domains] or \
           url.strip('/') in [f"https://{d}" for d in generic_domains] or \
           url.strip('/') in [f"http://{d}" for d in generic_domains]:
               
               # Create a direct search query url for India.gov.in
               name_encoded = urllib.parse.quote_plus(str(row['scheme_name']))
               if 'myscheme.gov.in' in url:
                   return f"https://www.myscheme.gov.in/search?q={name_encoded}"
               else:
                   return f"https://www.india.gov.in/search/site/{name_encoded}"
    
    if url == 'nan' or url == '':
        name_encoded = urllib.parse.quote_plus(str(row['scheme_name']))
        return f"https://www.myscheme.gov.in/search?q={name_encoded}"
        
    return url

df['application_url'] = df.apply(improve_url, axis=1)

# Print a sample of fixed URLs
print("\nSample of fixed Application URLs:")
for i, url in enumerate(df['application_url'].head(10)):
    print(f" - {url}")

# Save the modifications
df.to_csv(csv_path, index=False)
print("\nFixed CSV saved successfully!")
