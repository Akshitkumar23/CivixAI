"""
enrich_processed.py – Adds new enrichment columns to eligibility_train.csv
by joining with schemes_master.csv on scheme_id
"""
import csv
import sys

MASTER  = r'c:\Users\akshi\Desktop\CivixAI\data\master\schemes_master.csv'
TRAIN   = r'c:\Users\akshi\Desktop\CivixAI\data\processed\eligibility_train.csv'
BACKUP  = r'c:\Users\akshi\Desktop\CivixAI\data\processed\eligibility_train.pre_form_backup.csv'

NEW_COLS = ['gender_eligibility', 'caste_eligibility', 'disability_required',
            'occupation_eligibility', 'benefit_amount', 'tags', 'real_description',
            'education_level_required', 'urban_rural_eligibility', 
            'marital_status_required', 'employment_type_eligibility', 'is_bpl_only',
            'application_deadline', 'processing_time', 'popularity_score', 'is_scheme_active']

# ─── Load master lookup ────────────────────────────────────────────────────────
def load_master(path):
    lookup = {}
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row.get('scheme_id', '').strip()
            if sid:
                lookup[sid] = {c: row.get(c, '') for c in NEW_COLS}
    return lookup

# ─── Enrich a single CSV ──────────────────────────────────────────────────────
def enrich_csv(input_path, output_path, master_lookup, id_col):
    rows = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        old_fields = list(reader.fieldnames)

        # Remove existing new cols to avoid duplication on re-run
        for c in NEW_COLS:
            if c in old_fields:
                old_fields.remove(c)
        fieldnames = old_fields + NEW_COLS

        matched = 0
        for row in reader:
            sid = row.get(id_col, '').strip()
            enrichment = master_lookup.get(sid, {c: '' for c in NEW_COLS})
            for c in NEW_COLS:
                row[c] = enrichment.get(c, '')
            if enrichment.get('gender_eligibility'):
                matched += 1
            rows.append(row)

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    return len(rows), matched

# ─── Main ─────────────────────────────────────────────────────────────────────
print("Loading master lookup...")
lookup = load_master(MASTER)
print(f"  ✅ Loaded {len(lookup)} schemes from master")

# Enrich eligibility_train.csv  (id col = 'scheme_id')
print("\nEnriching eligibility_train.csv...")
total, matched = enrich_csv(TRAIN, TRAIN, lookup, 'scheme_id')
print(f"  ✅ {total:,} rows processed, {matched:,} scheme-rows matched ({matched/total*100:.1f}%)")

# Enrich pre_form_backup.csv  (id col = 'scheme_id')
print("\nEnriching eligibility_train.pre_form_backup.csv...")
total2, matched2 = enrich_csv(BACKUP, BACKUP, lookup, 'scheme_id')
print(f"  ✅ {total2:,} rows processed, {matched2:,} scheme-rows matched ({matched2/total2*100:.1f}%)")

print("\n🎉 All done! Both processed CSVs now have the new enrichment columns.")
