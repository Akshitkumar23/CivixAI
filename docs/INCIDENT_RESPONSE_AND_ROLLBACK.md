# CivixAI Incident Response, Monitoring & Rollback Runbook
> **Standard Operating Procedures for Platform Incidents, Evidence Inconsistencies, and Deployment Rollbacks.**  
> **Last Updated:** September 2026

---

## 1. INCIDENT SEVERITY CLASSIFICATION

| Severity | Description | Examples | Target MTTR |
| :--- | :--- | :--- | :--- |
| **P0 — Critical** | Complete service outage, deterministic rule safety violation, or corrupted audit hash chain. | - AST evaluator down or returning HTTP 500.<br>- Ineligible citizen falsely marked `ELIGIBLE` for a high-value subsidy.<br>- Claim-evidence hash chain broken. | **< 30 minutes** |
| **P1 — High** | Major functional degradation or verified external connector failure. | - Discovery crawler failing across >50% of state portals.<br>- Adaptive questionnaire session storage unavailable.<br>- Database latency > 500ms. | **< 2 hours** |
| **P2 — Medium** | Partial degradation with graceful fallback active. | - Python FastAPI offline, client-side fallback `src/lib/logic.ts` serving matches.<br>- Gemini chatbot rate-limited. | **< 8 hours** |
| **P3 — Low** | Cosmetic or minor non-blocking issue. | - UI styling anomaly, minor translation string typo, non-blocking telemetry delay. | **Next Release Cycle** |

---

## 2. EMERGENCY ROLLBACK PROCEDURES

### 2.1 Blue/Green & Canary Traffic Reversion
If an incident is detected following a production deployment:

1. **Immediate Traffic Cutover:**
   ```bash
   # In Kubernetes / Ingress Controller:
   kubectl set env deployment/civix-ingress ACTIVE_DEPLOYMENT=blue
   # Or in Cloudflare / Reverse Proxy:
   # Shift 100% traffic to previous stable release tag
   ```
2. **Container Image Rollback:**
   ```bash
   # Identify last stable release tag:
   docker pull ghcr.io/civixai/civix-core:stable-v2.0.0
   docker tag ghcr.io/civixai/civix-core:stable-v2.0.0 ghcr.io/civixai/civix-core:latest
   docker compose up -d --no-deps civix-backend
   ```
3. **Database Migration Rollback (if schema change failed):**
   ```bash
   # Run backward migration script
   python scripts/rollback_schema_migration.py --target-version v9
   ```

---

## 3. EVIDENCE INTEGRITY & DATA FREEZE KILL-SWITCH

If synthetic evidence, hallucinated Gazette criteria, or broken source citations are discovered:

1. **Activate Data Freeze Kill-Switch:**
   Set the following environment variable in production `.env`:
   ```env
   DATA_INGESTION_FROZEN=true
   AUTO_PROMOTION_BLOCKED=true
   ```
2. **Quarantine Affected Scheme:**
   ```bash
   # Immediately update scheme status to QUARANTINED in database:
   python scripts/quarantine_scheme.py --scheme-id [SUSPECT_SCHEME_ID] --reason "SYNTHETIC_EVIDENCE_DETECTED"
   ```
3. **Audit Ledger Verification:**
   Run `python -c "from services.core.evidence.claim_evidence_logger import ClaimEvidenceLogger; print(ClaimEvidenceLogger().verify_integrity())"` to ensure the cryptographic audit chain has not been compromised.

---

## 4. DORA METRICS & MONITORING TELEMETRY

The production cluster monitors four core DORA metrics:

1. **Deployment Frequency:** Target ≥ 1 production release per week; continuous deployment to staging.
2. **Lead Time for Changes:** Target < 24 hours from PR merge to production rollout.
3. **Change Failure Rate:** Target < 5% across production builds.
4. **Mean Time to Recovery (MTTR):** Target < 30 minutes for P0/P1 incidents via automated canary rollbacks.

---

## 5. INCIDENT POSTMORTEM TEMPLATE

Every P0/P1 incident mandates a blameless postmortem within 48 hours:

```markdown
# Incident Postmortem: [INCIDENT_TITLE]
- **Date & Time:** YYYY-MM-DD HH:MM UTC
- **Duration:** XX minutes
- **Severity:** P0 / P1
- **Impact:** [Number of users or schemes affected]
- **Root Cause:** [Technical summary of failure]
- **Detection:** [How was it detected? Alert vs citizen report]
- **Resolution:** [Action taken to resolve / rollback]
- **Corrective Actions:**
  1. [Action 1: Prevent recurrence]
  2. [Action 2: Enhance test coverage]
  3. [Action 3: Update documentation]
```
