import csv
import re

MASTER = r'c:\Users\akshi\Desktop\CivixAI\data\master\schemes_master.csv'

def advanced_enrich():
    rows = []
    with open(MASTER, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames)
        
        # Add NEW advanced columns if not present
        new_cols = [
            'education_level_required', 
            'urban_rural_eligibility', 
            'marital_status_required', 
            'employment_type_eligibility',
            'is_bpl_only'
        ]
        for col in new_cols:
            if col not in fieldnames:
                fieldnames.append(col)
        
        noise_keywords = ['vision & mission', 'nodal officers', 'read more about', 'census of india', 'payments to contractual staff']
        
        for row in reader:
            name = row['scheme_name'].lower()
            desc = row['real_description'].lower()
            cat = row['scheme_category'].lower()
            
            # 1. Skip Noise (Data Cleaning)
            if any(k in name for k in noise_keywords):
                continue
            
            # 2. Advanced Income Limit Logic (if blank)
            if not row['income_limit'].strip() or row['income_limit'] == 'nan':
                if 'education' in cat or 'scholarship' in name:
                    row['income_limit'] = '800000'
                elif 'housing' in cat:
                    row['income_limit'] = '600000'
                elif 'pension' in cat:
                    row['income_limit'] = '200000'
                elif 'farmer' in name or 'agriculture' in cat:
                    row['income_limit'] = '300000'
                else:
                    row['income_limit'] = '800000' # Government default for EWS/OBC-NCL

            # 3. Age Range Logic (if blank)
            if not row['min_age'].strip() or row['min_age'] == 'nan':
                if 'education' in cat: row['min_age'] = '5'
                elif 'pension' in cat: row['min_age'] = '60'
                elif 'employment' in cat or 'business' in cat: row['min_age'] = '18'
                else: row['min_age'] = '0'

            if not row['max_age'].strip() or row['max_age'] == 'nan':
                if 'education' in cat: row['max_age'] = '30'
                elif 'pension' in cat: row['max_age'] = '120'
                elif 'employment' in cat or 'business' in cat: row['max_age'] = '50'
                else: row['max_age'] = '100'

            # 4. Special Conditions Extraction
            conds = []
            if 'widow' in name or 'widow' in desc: conds.append('isWidow')
            if 'single girl' in name or 'single girl' in desc: conds.append('isSingleGirlChild')
            if 'disability' in name or 'disability' in desc or row['disability_required'] == 'true': conds.append('hasDisability')
            if 'minority' in name or 'minority' in desc or row['caste_eligibility'] == 'Minority': conds.append('isMinority')
            if 'bpl' in name or 'bpl' in desc or 'economically weaker' in desc: conds.append('isBPL')
            
            if conds:
                row['special_conditions_required'] = ",".join(conds)

            # 5. Populate NEW Columns
            # Education Level
            if 'post matric' in name or 'post-matric' in name: row['education_level_required'] = '10th_pass'
            elif 'fellowship' in name or 'ph.d' in name: row['education_level_required'] = 'graduate'
            elif 'scholarship' in name: row['education_level_required'] = 'none' # Usually school level
            else: row['education_level_required'] = 'any'

            # Urban/Rural
            if 'grameen' in name or 'rural' in name or 'rural' in desc: row['urban_rural_eligibility'] = 'rural'
            elif 'shehari' in name or 'urban' in name or 'urban' in desc: row['urban_rural_eligibility'] = 'urban'
            else: row['urban_rural_eligibility'] = 'both'

            # Marital Status
            if 'widow' in name: row['marital_status_required'] = 'widowed'
            elif 'maternity' in name or 'marriage' in name: row['marital_status_required'] = 'married'
            else: row['marital_status_required'] = 'any'

            # Employment Type
            if 'unorganised' in name or 'informal' in name: row['employment_type_eligibility'] = 'informal'
            elif 'salaried' in name or 'epf' in name: row['employment_type_eligibility'] = 'salaried'
            elif 'self employed' in name or 'business' in cat: row['employment_type_eligibility'] = 'self_employed'
            else: row['employment_type_eligibility'] = 'any'

            # BPL Only flag
            row['is_bpl_only'] = 'true' if 'bpl' in name or 'bpl' in desc else 'false'

            rows.append(row)

    # Write back
    with open(MASTER, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Advanced Enrichment Complete. Processed {len(rows)} schemes.")

if __name__ == "__main__":
    advanced_enrich()
