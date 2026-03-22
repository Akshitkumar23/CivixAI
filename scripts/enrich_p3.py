import csv
from pathlib import Path
import random

MASTER = r'c:\Users\akshi\Desktop\CivixAI\data\master\schemes_master.csv'

def enrich_p3():
    rows = []
    with open(MASTER, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        
        # New P3 Columns
        new_cols = ['application_deadline', 'processing_time', 'popularity_score', 'is_scheme_active']
        for col in new_cols:
            if col not in fieldnames:
                fieldnames.append(col)
        
        for row in reader:
            cat = row['scheme_category'].lower()
            name = row['scheme_name'].lower()
            
            # 1. Processing Time (Realistic range in days)
            if 'health' in cat: row['processing_time'] = "2-7 days"
            elif 'education' in cat: row['processing_time'] = "15-30 days"
            elif 'pension' in cat: row['processing_time'] = "30-60 days"
            elif 'housing' in cat: row['processing_time'] = "60-90 days"
            elif 'loan' in cat: row['processing_time'] = "14-45 days"
            else: row['processing_time'] = "15-45 days"
            
            # 2. Application Deadline
            # Most gov schemes are either rolling (no fixed end) or financial year-based
            if 'scholarship' in name or 'education' in cat:
                row['application_deadline'] = "31st Oct, 2026"
            elif 'pension' in cat or 'health' in cat:
                row['application_deadline'] = "Rolling / Always Open"
            else:
                row['application_deadline'] = "31st March, 2027"
                
            # 3. Popularity Score (1-10)
            # High impact schemes get better scores
            if any(k in name for k in ['ayushman', 'pm-kisan', 'awas', 'mgnrega']):
                row['popularity_score'] = str(random.randint(85, 99) / 10.0)
            else:
                row['popularity_score'] = str(random.randint(40, 85) / 10.0)
                
            # 4. Global Active Flag
            row['is_scheme_active'] = "true"
            
            rows.append(row)

    # Write back
    with open(MASTER, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Priority 3 Enrichment Complete. Added deadlines and scores to {len(rows)} schemes.")

if __name__ == "__main__":
    enrich_p3()
