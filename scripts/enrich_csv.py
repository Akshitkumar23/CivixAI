import csv
import re

def determine_gender_eligibility(name, desc):
    text = (name + ' ' + desc).lower()
    female_kw = ['women', 'girl', 'widow', 'mahila', 'female', 'maternity',
                 'pregnant', 'mother', 'beti', 'single girl', 'woman', 'ladies',
                 'shakti', 'suraksha', 'shishu', 'janani', 'pradhan mantri poshan']
    for kw in female_kw:
        if kw in text:
            return 'female'
    return 'all'

def determine_caste_eligibility(name, desc):
    text = (name + ' ' + desc).lower()
    castes = []
    if 'scheduled caste' in text or re.search(r'\bsc\b', text) or 'sc/st' in text or 'sc and st' in text:
        castes.append('SC')
    if 'scheduled tribe' in text or re.search(r'\bst\b', text) or 'sc/st' in text or 'tribal' in text:
        castes.append('ST')
    if 'obc' in text or 'other backward' in text:
        castes.append('OBC')
    if 'ebc' in text or 'economically backward' in text:
        castes.append('EBC')
    if 'dnt' in text or 'denotified' in text or 'nomadic' in text:
        castes.append('DNT')
    if 'minority' in text:
        castes.append('Minority')
    if castes:
        return ','.join(list(dict.fromkeys(castes)))
    return 'all'

def determine_disability_required(name, desc):
    text = (name + ' ' + desc).lower()
    kws = ['disab', 'pwd', 'handicap', 'differently abled', 'divyang',
           'blind', 'deaf', 'locomotor', 'visual impair', 'saksham']
    return 'true' if any(k in text for k in kws) else 'false'

def determine_occupation_eligibility(category, name):
    n = name.lower()
    c = category.lower()
    occ = []
    if c == 'agriculture' or any(k in n for k in ['farmer','kisan','agricultural','farm','krishi','fisheries','matsya','horticulture']):
        occ.append('farmer')
    if c == 'education' or any(k in n for k in ['student','scholarship','fellowship','apprentice','intern','nats','doctoral']):
        occ.append('student')
    if c == 'employment' or any(k in n for k in ['skill','job','employment','labour','worker','nrega','kaushal']):
        occ.append('unemployed')
    if any(k in n for k in ['msme','entrepreneur','business','startup','self employ','proprietor','artisan','prism','acabc']):
        occ.append('self_employed')
    if any(k in n for k in ['sportsperson','athlete','sport','khelo']):
        occ.append('athlete')
    return ','.join(list(dict.fromkeys(occ))) if occ else 'all'

def determine_tags(name, category, ministry):
    n = name.lower()
    m = ministry.lower()
    tags = []

    cat_tag_map = {
        'education': ['education', 'scholarship'],
        'health': ['health', 'medical'],
        'agriculture': ['agriculture', 'farming'],
        'employment': ['employment', 'skill', 'jobs'],
        'housing': ['housing', 'shelter'],
        'pension': ['pension', 'elderly', 'social_security'],
        'women_welfare': ['women', 'gender', 'empowerment'],
        'infrastructure': ['infrastructure', 'development'],
        'general_welfare': ['welfare', 'social'],
        'insurance': ['insurance', 'coverage'],
    }
    tags.extend(cat_tag_map.get(category, ['welfare']))

    keyword_tags = {
        'sc': 'SC', 'scheduled caste': 'SC', 'obc': 'OBC', 'tribal': 'ST,tribal',
        'widow': 'widow', 'disab': 'disability,PWD', 'divyang': 'disability,PWD',
        'rural': 'rural', 'grameen': 'rural', 'gramin': 'rural', 'urban': 'urban',
        'bpl': 'BPL', 'dbt': 'DBT', 'loan': 'loan', 'credit': 'loan', 'mudra': 'loan',
        'pension': 'pension', 'insurance': 'insurance', 'bima': 'insurance',
        'housing': 'housing', 'awas': 'housing', 'north east': 'northeast',
        'farmer': 'farmer', 'kisan': 'farmer', 'fish': 'fisherman',
        'sports': 'sports', 'youth': 'youth', 'digital': 'digital', 'startup': 'startup',
        'msme': 'MSME', 'research': 'research', 'science': 'science',
    }
    for kw, tag in keyword_tags.items():
        if kw in n:
            for t in tag.split(','):
                tags.append(t)

    return ','.join(list(dict.fromkeys(tags)))

KNOWN_AMOUNTS = {
    'pm kisan': '₹6,000/year (₹2,000 × 3 installments)',
    'pradhan mantri kisan samman': '₹6,000/year',
    'ayushman bharat': '₹5 lakh/year (hospitalization cover)',
    'pmjay': '₹5 lakh/year (health cover)',
    'ab-pmjay': '₹5 lakh/year (health cover)',
    'pradhan mantri awas yojna grameen': '₹1.20 lakh (plain) / ₹1.30 lakh (hilly area)',
    'mahatma gandhi nrega': 'Daily wage (₹200–₹353 by state)',
    'atal pension': '₹1,000–₹5,000/month pension',
    'indira gandhi national old age': '₹200–₹500/month',
    'indira gandhi national widow': '₹200–₹300/month',
    'pradhan mantri fasal bima': 'Up to 100% crop value insured',
    'janani suraksha': '₹1,400 (rural) / ₹1,000 (urban)',
    'pradhan mantri vaya vandana': 'Up to ₹9,250/month pension',
    'pradhan mantri kisan mandhan': '₹3,000/month pension after 60',
    'swachh bharat': '₹12,000 (toilet construction)',
    'deen dayal upadhyay grameen kaushalya': 'Free training + placement support',
    'national family benefit': '₹30,000 lump sum',
    'national means-cum-merit scholarship': '₹12,000/year',
    'khelo india': 'Annual scholarship up to ₹5 lakh',
    'pension to meritorious sportspersons': '₹1,000–₹3,000/month',
    'special cash awards to medal winners': 'Lump sum (up to ₹75 lakh for Olympics gold)',
    'pradhan mantri matsya sampada': 'Up to ₹3 lakh subsidy (60% for women)',
    'nikshay': '₹500/month nutritional support',
    'national scholarship for post-graduate': '₹3,100–₹3,500/month',
    'national means': '₹12,000/year',
}

def determine_benefit_amount(name, category):
    n = name.lower()
    for key, amt in KNOWN_AMOUNTS.items():
        if key in n:
            return amt
    defaults = {
        'education': 'Scholarship amount varies',
        'pension': '₹200–₹5,000/month',
        'health': 'Medical coverage/subsidy',
        'housing': 'Construction subsidy varies',
        'employment': 'Wage/stipend varies',
        'agriculture': 'Subsidy/financial aid varies',
        'insurance': 'Coverage varies by scheme',
        'women_welfare': 'Financial aid/subsidy varies',
    }
    return defaults.get(category, 'Varies — refer official portal')

def improve_description(name, category, ministry):
    cat_desc = {
        'education': f"{name} — Provides educational support such as scholarships, fellowships, or stipends to eligible students to reduce financial burden and improve access to higher education. Administered by {ministry}.",
        'health': f"{name} — Ensures affordable access to healthcare through medical coverage, hospitalization, or maternity benefits for eligible citizens. Implemented by {ministry}.",
        'agriculture': f"{name} — Supports farmers and agricultural workers with financial aid, subsidies, or technical assistance to boost productivity and secure rural livelihoods. Administered by {ministry}.",
        'employment': f"{name} — Facilitates job creation, skill upgradation, or guaranteed wage employment to improve livelihood opportunities for youth and workers. Run by {ministry}.",
        'housing': f"{name} — Provides financial assistance or subsidized credit for construction, purchase, or renovation of houses for economically weaker sections. Managed by {ministry}.",
        'pension': f"{name} — Ensures monthly pension disbursements to provide social security for elderly, widows, or differently-abled citizens in need. Operated by {ministry}.",
        'insurance': f"{name} — Provides affordable insurance coverage or financial protection against health, crop, or life-related risks for eligible beneficiaries. Managed by {ministry}.",
        'women_welfare': f"{name} — Designed to empower women through targeted financial aid, educational support, or health benefits to promote gender equity. Managed by {ministry}.",
        'infrastructure': f"{name} — Focuses on rural or urban infrastructure development to improve access to essential services like roads, sanitation, and water. Implemented by {ministry}.",
        'general_welfare': f"{name} — Provides targeted welfare support and specialized benefits to uplift eligible citizens across various demographics. Implemented by {ministry}.",
    }
    return cat_desc.get(category, f"{name} — A government welfare scheme providing targeted benefits to eligible citizens. Administered by {ministry}.")

# ─── Main Processing ───────────────────────────────────────────────────────────
INPUT  = r'c:\Users\akshi\Desktop\CivixAI\data\master\schemes_master.csv'
OUTPUT = r'c:\Users\akshi\Desktop\CivixAI\data\master\schemes_master.csv'

new_cols = ['gender_eligibility', 'caste_eligibility', 'disability_required',
            'occupation_eligibility', 'benefit_amount', 'tags', 'real_description']

rows = []
with open(INPUT, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    old_fields = list(reader.fieldnames)

    # Remove existing new cols to avoid duplication on re-run
    for c in new_cols:
        if c in old_fields:
            old_fields.remove(c)
    fieldnames = old_fields + new_cols

    for row in reader:
        name     = row.get('scheme_name', '')
        desc     = row.get('benefit_description', '')
        category = row.get('scheme_category', '')
        ministry = row.get('ministry', '')
        b_type   = row.get('benefit_type', 'scheme')

        row['gender_eligibility']     = determine_gender_eligibility(name, desc)
        row['caste_eligibility']       = determine_caste_eligibility(name, desc)
        row['disability_required']     = determine_disability_required(name, desc)
        row['occupation_eligibility']  = determine_occupation_eligibility(category, name)
        row['benefit_amount']          = determine_benefit_amount(name, category)
        row['tags']                    = determine_tags(name, category, ministry)
        row['real_description']        = improve_description(name, category, ministry)

        rows.append(row)

with open(OUTPUT, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ Done! Enriched {len(rows)} schemes with {len(new_cols)} new columns.")

# Quick Stats
from collections import Counter
print("\n📊 Gender Distribution:", Counter(r['gender_eligibility'] for r in rows))
print("📊 Caste Distribution:", Counter(r['caste_eligibility'] for r in rows).most_common(5))
print("📊 Disability Required:", Counter(r['disability_required'] for r in rows))
print("📊 Top Occupations:", Counter(r['occupation_eligibility'] for r in rows).most_common(5))
