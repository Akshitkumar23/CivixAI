# CivixAI — Scheme Discovery & Ingestion Architecture

## 1. Overview & Strict Trust Boundary
CivixAI expands its official scheme coverage across India's Central, State, and Union Territory jurisdictions using a **registry-driven discovery and ingestion platform**. 

### The Core Architectural Invariant
```
DISCOVERY & FETCHING ≠ POLICY CERTIFICATION
```
Under no circumstances may automated scrapers, OCR workers, or LLM extractors write authoritative records to `eligibility_rules` or mark schemes as `certified`. Automated connectors discover, fetch, snapshot, and generate draft review packets. **Human policy analysts and governance officers retain sole authority to certify statutory eligibility rules.**

---

## 2. Pool Separation Model

To prevent unreviewed metadata records from masquerading as verified legal entitlements, CivixAI establishes four segregated scheme pools:

| Pool Name | Criteria | Permitted Verdicts | Frontend Visibility |
| :--- | :--- | :--- | :--- |
| **AUTHORITATIVE_ELIGIBILITY_POOL** | Active citizen schemes with published, human-certified AST rules. | `ELIGIBLE`, `NEEDS_INFO`, `NEEDS_VERIFICATION`, `NOT_ELIGIBLE` | Primary Results View ("Eligible Now" + "Potential Matches") |
| **DISCOVERY_POOL** | Active unreviewed schemes discovered from official registries. | `DISCOVERED_NOT_EVALUATED` only | Dedicated "Discovered Schemes" tab with governance notice |
| **INSTITUTIONAL_POOL** | Non-citizen schemes (grants to NGOs, local bodies, institutions). | N/A | Excluded from citizen personal recommendations |
| **HISTORICAL_POOL** | Withdrawn, subsumed, or expired schemes. | `HISTORICAL_EXPIRED` | Lineage & Audit Archive |

---

## 3. Connector Interface

All official data sources are accessed through a unified interface (`services/scraper/connector.py`):

```python
class BaseSchemeConnector(abc.ABC):
    def discover(self, limit: int = 100) -> List[SchemeDiscoveryCandidate]:
        """Discovers candidates from public indexes without bypassing robots/auth."""

    def fetch(self, candidate: SchemeDiscoveryCandidate) -> Tuple[bool, str, Dict[str, Any]]:
        """Fetches public official HTML/PDF guidelines with HTTP health telemetry."""

    def snapshot(self, candidate_id: str, raw_content: str) -> str:
        """Stores immutable raw content snapshot with SHA-256 hash."""

    def parse(self, raw_content: str, content_type: str = "html") -> Dict[str, Any]:
        """Parses structured sections; flags OCR_REQUIRED for scanned PDFs."""

    def extract_metadata(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts candidate draft conditions, benefits, and required documents."""

    def detect_changes(self, existing_hash: str, new_hash: str) -> bool:
        """Detects policy amendments via SHA-256 hash comparison."""

    def generate_review_packet(self, candidate: SchemeDiscoveryCandidate) -> Dict[str, Any]:
        """Generates human review packet for governance certification."""
```

---

## 4. Official Discovery Sources & Current Universe Snapshot

Counts from official government portals are maintained separately and never summed naively because portals operate under differing component definitions:

1. **myScheme (`myscheme.gov.in`)**:
   - Authority: MeitY / NeGD / Digital India.
   - Reported Coverage: **3,450+ total schemes** (~520 Central, ~2,930 State/UT).
   - Character: Comprehensive citizen-facing service and scheme index.
2. **DBT Bharat (`dbtbharat.gov.in`)**:
   - Authority: Cabinet Secretariat DBT Mission.
   - Reported Coverage: **314 Central DBT schemes** across 53 Ministries.
   - Character: High-integrity direct benefit transfer cash/in-kind schemes.
3. **India.gov.in (`india.gov.in`)**:
   - Authority: National Informatics Centre (NIC).
   - Reported Coverage: **2,180+ citizen programmes and services**.
   - Character: Official national portal of the Indian Government.
4. **CivixAI Corpus**:
   - **135 Central schemes** (27 citizen-certified, 2 institutional, 104 unreviewed legacy, 1 withdrawn, 1 subsumed).
   - **0 State/UT schemes certified** (36 jurisdictions indexed in `data/state_ut_source_registry.json` for staged expansion).

---

## 5. Candidate Lifecycle & Conservative Deduplication

Candidates move through strict, audited lifecycle states:
```
DISCOVERED → SOURCE_CONFIRMED → FETCHED → PARSED → EXTRACTED → REVIEW_REQUIRED → CERTIFIED (Human)
     ↓                                                                     ↓
POSSIBLE_DUPLICATE                                                      REJECTED
```

### Conservative Identity Resolution
- Schemes are deduplicated using: official ministry/department code, normalized scheme name, official gazette URL, and benefit type.
- Never auto-merge ambiguous candidates. Ambiguous matches are flagged as `PENDING_IDENTITY_REVIEW`.
- Scheme versions, component schemes, renamed schemes, and sub-schemes are tracked as separate lineage nodes.

---

## 6. PDF / OCR Pipeline
When an official government guideline is available only as a scanned PDF:
1. `connector.parse()` sets `ocr_status = OCR_REQUIRED`.
2. OCR worker processes the document and generates plain text with an OCR quality confidence score (0.0 to 1.0).
3. Any low-confidence extraction (< 0.85) is flagged for manual transcription.
4. **Invariant:** No OCR-derived rule may auto-publish without human verification.

---

## 7. State & UT Expansion Architecture
`data/state_ut_source_registry.json` indexes all **28 States and 8 Union Territories (36 jurisdictions)**. Each entry records:
- State/UT portal and official scheme index portal.
- State DBT portal URL.
- Source quality tier (Tier 1: structured/DBT, Tier 2: departmental services, Tier 3: static circulars).
- Connector activation status (`STAGED_READY`).

Expansion proceeds in controlled batches:
1. **P0 Central Missing Schemes Queue** (`data/scheme_discovery_candidates.json`): MGNREGA, PMFBY, KCC, NFSA/PMGKAY, Sukanya Samriddhi, DAY-NRLM.
2. **Legacy 104 Remediation Queue** (`data/legacy_104_remediation_queue.json`): 104 legacy schemes undergoing official gazette re-discovery and rule extraction.
3. **State Flagship Batches**: High-impact state welfare transfers (e.g. Rythu Bharosa, Kalia, Gruha Lakshmi, Ladki Bahin).
