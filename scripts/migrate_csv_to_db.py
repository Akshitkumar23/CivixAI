"""
ETL Migration Script: Migrates schemes_master.csv into normalized relational SQLite/Postgres DB
"""
import re
import sys
import uuid
from pathlib import Path
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.core.database import SessionLocal, init_db
from services.core.database.models import (
    Scheme, SchemeVersion, Authority, Category,
    EligibilityRule, Benefit, DocumentRequirement, SourceDocument
)

def slugify(text: str) -> str:
    text = str(text).lower().strip()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def run_migration():
    if "--force-legacy-override" not in sys.argv:
        print("[DEPRECATED] migrate_csv_to_db.py is permanently deprecated to prevent unverified legacy CSV ingestion.")
        print("Direct canonical database insertion from legacy CSV is forbidden by P0 Governance Invariants.")
        print("Use the authoritative pipeline in 'services/core/ingestion/pipeline.py'.")
        print("Pass '--force-legacy-override --dry-run' or '--force-legacy-override --inspect' for non-mutating inspection.")
        sys.exit(0)

    # P0 Phase 7 Shield: Override cannot bypass statutory publication gates
    is_dry_run = "--dry-run" in sys.argv
    is_inspect = "--inspect" in sys.argv
    is_stage = "--stage" in sys.argv

    if not (is_dry_run or is_inspect or is_stage):
        print("P0 GOVERNANCE VIOLATION BLOCKED: Legacy override cannot publish canonical active/published scheme versions.")
        print("Permitted legacy modes: --dry-run, --inspect, --stage.")
        print("Direct publication of canonical active statutory versions is strictly blocked.")
        sys.exit(1)

    csv_path = PROJECT_ROOT / "data" / "master" / "schemes_master.csv"
    if not csv_path.exists():
        print(f"Error: CSV not found at {csv_path}")
        return

    df = pd.read_csv(csv_path)
    if is_inspect:
        print(f"[INSPECT] Found {len(df)} schemes in {csv_path}. Canonical publication disabled.")
        return

    print("Initializing database tables...")
    init_db()
    print(f"Loaded {len(df)} schemes from CSV. (Mode: {'dry-run' if is_dry_run else 'stage'})")

    session = SessionLocal()
    try:
        # 1. Populate standard Categories
        categories_dict = {}
        for cat_name in df["scheme_category"].dropna().unique():
            cat_slug = slugify(cat_name)
            cat_obj = session.query(Category).filter_by(id=cat_slug).first()
            if not cat_obj:
                cat_obj = Category(id=cat_slug, name=str(cat_name).title(), slug=cat_slug)
                session.add(cat_obj)
            categories_dict[str(cat_name).strip().lower()] = cat_slug

        # 2. Populate Authorities (Ministries)
        authorities_dict = {}
        for auth_name in df["ministry"].dropna().unique():
            auth_slug = slugify(auth_name)[:64]
            auth_obj = session.query(Authority).filter_by(id=auth_slug).first()
            if not auth_obj:
                auth_obj = Authority(id=auth_slug, name=str(auth_name).strip(), level="Central")
                session.add(auth_obj)
            authorities_dict[str(auth_name).strip().lower()] = auth_slug

        session.commit()

        # 3. Populate Schemes, Versions, Rules, and Benefits
        inserted_schemes = 0
        inserted_rules = 0

        for _, row in df.iterrows():
            scheme_id = str(row.get("scheme_id", "")).strip()
            if not scheme_id or pd.isna(scheme_id):
                scheme_id = slugify(row.get("scheme_name", ""))[:128]

            scheme_name = str(row.get("scheme_name", scheme_id)).strip()
            ministry = str(row.get("ministry", "")).strip().lower()
            category = str(row.get("scheme_category", "")).strip().lower()

            auth_id = authorities_dict.get(ministry)
            cat_id = categories_dict.get(category)

            raw_btype = str(row.get("benefit_type", "scheme")).lower()
            programme_kind = "loan" if "loan" in raw_btype else ("insurance" if "insurance" in raw_btype else "welfare")

            # Check if scheme already exists
            scheme_obj = session.query(Scheme).filter_by(id=scheme_id).first()
            if not scheme_obj:
                scheme_obj = Scheme(
                    id=scheme_id,
                    canonical_name=scheme_name,
                    authority_id=auth_id,
                    category_id=cat_id,
                    scheme_level=str(row.get("scheme_level", "Central")),
                    programme_kind=programme_kind,
                    status="draft",
                    is_active=False,
                    popularity_score=float(row.get("popularity_score", 5.0)) if pd.notna(row.get("popularity_score")) else 5.0
                )
                session.add(scheme_obj)
                session.flush()
                inserted_schemes += 1

            version_id = f"{scheme_id}-v1"
            version_obj = session.query(SchemeVersion).filter_by(id=version_id).first()
            if not version_obj:
                version_obj = SchemeVersion(
                    id=version_id,
                    scheme_id=scheme_id,
                    version_number=1,
                    status="draft",
                    verification_status="imported_unverified",
                    summary=str(row.get("benefit_description", ""))[:300],
                    description=str(row.get("benefit_description", "")),
                    application_url=str(row.get("application_url", "")),
                    source_url=str(row.get("source_url", "")),
                    processing_time=str(row.get("processing_time", "15-30 days")) if pd.notna(row.get("processing_time")) else "15-30 days"
                )
                session.add(version_obj)
                session.flush()

                # ── Generate Declarative Rules ──────────────────────────────
                # Rule 1: Age Range
                min_age = row.get("min_age")
                max_age = row.get("max_age")
                if pd.notna(min_age) and pd.notna(max_age) and (min_age > 0 or max_age < 100):
                    rule = EligibilityRule(
                        id=str(uuid.uuid4()),
                        scheme_version_id=version_id,
                        rule_group="default",
                        fact_key="person.age",
                        operator="between",
                        expected_value=f"[{int(min_age)}, {int(max_age)}]",
                        mandatory=True,
                        reason_code="AGE_ELIGIBILITY"
                    )
                    session.add(rule)
                    inserted_rules += 1

                # Rule 2: Income Limit
                income_limit = row.get("income_limit")
                if pd.notna(income_limit) and float(income_limit) > 0:
                    rule = EligibilityRule(
                        id=str(uuid.uuid4()),
                        scheme_version_id=version_id,
                        rule_group="default",
                        fact_key="household.annual_income",
                        operator="lte",
                        expected_value=str(float(income_limit)),
                        mandatory=True,
                        reason_code="INCOME_LIMIT"
                    )
                    session.add(rule)
                    inserted_rules += 1

                # Rule 3: Applicable States
                states = str(row.get("applicable_states", "ALL")).strip()
                if states and states.upper() != "ALL":
                    state_list = [s.strip() for s in states.split(",") if s.strip()]
                    rule = EligibilityRule(
                        id=str(uuid.uuid4()),
                        scheme_version_id=version_id,
                        rule_group="default",
                        fact_key="location.state",
                        operator="in",
                        expected_value=str(state_list),
                        mandatory=True,
                        reason_code="STATE_DOMICILE"
                    )
                    session.add(rule)
                    inserted_rules += 1

                # Rule 4: Caste Eligibility
                caste = str(row.get("caste_eligibility", "all")).strip()
                if caste and caste.lower() != "all":
                    caste_list = [c.strip().lower() for c in caste.split(",") if c.strip()]
                    rule = EligibilityRule(
                        id=str(uuid.uuid4()),
                        scheme_version_id=version_id,
                        rule_group="default",
                        fact_key="social.caste",
                        operator="in",
                        expected_value=str(caste_list),
                        mandatory=True,
                        reason_code="CASTE_ELIGIBILITY"
                    )
                    session.add(rule)
                    inserted_rules += 1

                # Rule 5: Gender Eligibility
                gender = str(row.get("gender_eligibility", "all")).strip()
                if gender and gender.lower() != "all":
                    gender_list = [g.strip().lower() for g in gender.split(",") if g.strip()]
                    rule = EligibilityRule(
                        id=str(uuid.uuid4()),
                        scheme_version_id=version_id,
                        rule_group="default",
                        fact_key="person.gender",
                        operator="in",
                        expected_value=str(gender_list),
                        mandatory=True,
                        reason_code="GENDER_ELIGIBILITY"
                    )
                    session.add(rule)
                    inserted_rules += 1

                # Rule 6: Occupation Eligibility
                occupation = str(row.get("occupation_eligibility", "all")).strip()
                if occupation and occupation.lower() != "all":
                    occ_list = [o.strip().lower() for o in occupation.split(",") if o.strip()]
                    rule = EligibilityRule(
                        id=str(uuid.uuid4()),
                        scheme_version_id=version_id,
                        rule_group="default",
                        fact_key="occupation.type",
                        operator="in",
                        expected_value=str(occ_list),
                        mandatory=True,
                        reason_code="OCCUPATION_ELIGIBILITY"
                    )
                    session.add(rule)
                    inserted_rules += 1

                # Rule 7: Disability Required
                disability_req = row.get("disability_required")
                if pd.notna(disability_req) and str(disability_req).lower() in ("true", "1", "yes"):
                    rule = EligibilityRule(
                        id=str(uuid.uuid4()),
                        scheme_version_id=version_id,
                        rule_group="default",
                        fact_key="health.has_disability",
                        operator="eq",
                        expected_value="True",
                        mandatory=True,
                        reason_code="DISABILITY_REQUIRED"
                    )
                    session.add(rule)
                    inserted_rules += 1

                # Rule 8: BPL Only
                bpl_only = row.get("is_bpl_only")
                if pd.notna(bpl_only) and str(bpl_only).lower() in ("true", "1", "yes"):
                    rule = EligibilityRule(
                        id=str(uuid.uuid4()),
                        scheme_version_id=version_id,
                        rule_group="default",
                        fact_key="social.is_bpl",
                        operator="eq",
                        expected_value="True",
                        mandatory=True,
                        reason_code="BPL_REQUIRED"
                    )
                    session.add(rule)
                    inserted_rules += 1

                # ── Benefit Record ──────────────────────────────────────────
                b_amount = row.get("benefit_amount")
                fixed_val = None
                if pd.notna(b_amount):
                    try:
                        fixed_val = float(str(b_amount).replace(",", "").replace("₹", "").strip())
                    except ValueError:
                        pass

                benefit = Benefit(
                    id=str(uuid.uuid4()),
                    scheme_version_id=version_id,
                    benefit_type=raw_btype,
                    amount_type="fixed" if fixed_val else "description",
                    fixed_amount=fixed_val,
                    description=str(row.get("benefit_description", ""))
                )
                session.add(benefit)

                # ── Document Requirements ───────────────────────────────────
                raw_docs = str(row.get("documents_required", ""))
                if raw_docs and pd.notna(raw_docs) and raw_docs.lower() != "nan":
                    for d in raw_docs.split(","):
                        d = d.strip()
                        if d:
                            doc_req = DocumentRequirement(
                                id=str(uuid.uuid4()),
                                scheme_version_id=version_id,
                                document_type=d,
                                is_mandatory=True
                            )
                            session.add(doc_req)

                # ── Source Document ─────────────────────────────────────────
                src_url = str(row.get("source_url", row.get("application_url", "")))
                if src_url and src_url.lower() != "nan":
                    src_doc = SourceDocument(
                        id=str(uuid.uuid4()),
                        scheme_version_id=version_id,
                        url=src_url,
                        publisher=str(row.get("ministry", "Government of India")),
                        trust_level="A"
                    )
                    session.add(src_doc)

        if is_dry_run:
            session.rollback()
            print(f"[DRY-RUN] Success! Simulated staging of {inserted_schemes} schemes and {inserted_rules} rules. All transactions rolled back.")
        else:
            session.commit()
            print(f"[STAGE] Complete! Staged {inserted_schemes} unreviewed draft schemes (status=draft, verification_status=imported_unverified).")

    except Exception as e:
        session.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    run_migration()
