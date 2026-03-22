import csv
from collections import Counter

master = r'c:\Users\akshi\Desktop\CivixAI\data\master\schemes_master.csv'
with open(master, encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

print(f'Total schemes: {len(rows)}')
print()

cols = list(rows[0].keys())
print('=== MISSING / BLANK VALUES PER COLUMN ===')
for c in cols:
    blank = sum(1 for r in rows if not r[c].strip() or r[c].strip() in ('nan',''))
    print(f'  {c:<45} missing: {blank:>3} / {len(rows)}')

print()
print('=== VALUE DISTRIBUTIONS ===')
for c in ['gender_eligibility','caste_eligibility','disability_required','occupation_eligibility','scheme_category','benefit_type']:
    ctr = Counter(r[c].strip() for r in rows)
    print(f'  [{c}]')
    for val, cnt in ctr.most_common(10):
        print(f'    {val!r:<30} {cnt}')

print()
filled_income = sum(1 for r in rows if r['income_limit'].strip() and r['income_limit'].strip() not in ('nan',''))
print(f'income_limit filled:               {filled_income}/{len(rows)}')

state_specific = sum(1 for r in rows if r['applicable_states'].strip() not in ('ALL','nan',''))
print(f'state-specific (not ALL/blank):    {state_specific}/{len(rows)}')

filled_app_url = sum(1 for r in rows if r['application_url'].strip())
print(f'application_url filled:            {filled_app_url}/{len(rows)}')

filled_special = sum(1 for r in rows if r['special_conditions_required'].strip())
print(f'special_conditions filled:         {filled_special}/{len(rows)}')

specific_amount = sum(1 for r in rows if r['benefit_amount'].strip() and 'Varies' not in r['benefit_amount'] and r['benefit_amount'].strip())
print(f'benefit_amount specific (not generic): {specific_amount}/{len(rows)}')

tags_multi = sum(1 for r in rows if ',' in r['tags'])
print(f'tags with multiple values:         {tags_multi}/{len(rows)}')
