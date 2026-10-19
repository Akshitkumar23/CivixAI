import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const ML_SERVICE_URL = process.env.ML_API_URL || 'http://127.0.0.1:8000';

async function fetchDetailFallback(id: string) {
  return new Promise((resolve, reject) => {
    const pyExe = path.join(process.cwd(), '.venv', 'Scripts', 'python.exe');
    const args = [
      '-c',
      `
import sys, json, sqlite3
from pathlib import Path

conn = sqlite3.connect('data/civix.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

target_id = "${id}".strip()
cur.execute("SELECT * FROM programme_discovery WHERE programme_id = ? OR canonical_name LIKE ? LIMIT 1", (target_id, f"%{target_id}%"))
row = cur.fetchone()
conn.close()

if not row:
    print(json.dumps({"error": "Programme not found"}))
    sys.exit(0)

r = dict(row)
p_type = r.get("programme_type") or "SCHEME"
jur = r.get("jurisdiction") or "CENTRAL"
gov_level = "Central" if jur == "CENTRAL" else ("UT" if jur == "UT" else "State")
estatus = r.get("eligibility_status") or "INSUFFICIENT_OFFICIAL_EVIDENCE"
is_cert = bool(r.get("is_certified"))

if estatus == "ELIGIBILITY_READY" or is_cert:
    elig_label = "✓ Eligibility verified"
    banner_msg = "Eligibility verification available"
    banner_type = "SUCCESS"
elif estatus == "ELIGIBILITY_REVIEW":
    elig_label = "Eligibility review pending"
    banner_msg = "Eligibility rules are under official review."
    banner_type = "REVIEW"
elif estatus == "INSUFFICIENT_OFFICIAL_EVIDENCE":
    elig_label = "Official evidence unavailable"
    banner_msg = "Eligibility verification is currently unavailable because sufficient official evidence has not been verified."
    banner_type = "UNAVAILABLE"
elif estatus in ("INSTITUTIONAL_ONLY", "EMPLOYER_ONLY") or p_type in ("INSTITUTIONAL_PROGRAMME", "EMPLOYER_PROGRAMME"):
    elig_label = "Institution / Employer programme"
    banner_msg = "This programme is an institutional or employer scheme and does not evaluate individual citizen eligibility."
    banner_type = "SCOPE"
elif estatus == "INFORMATIONAL" or p_type == "INFORMATIONAL_PROGRAMME":
    elig_label = "Informational"
    banner_msg = "This is an informational programme; no direct citizen welfare application is required."
    banner_type = "SCOPE"
elif estatus == "SERVICE" or "SERVICE" in p_type:
    elig_label = "Service"
    banner_msg = "This is a public service or portal registration programme."
    banner_type = "SCOPE"
else:
    elig_label = "Official evidence unavailable"
    banner_msg = "Eligibility verification is currently unavailable."
    banner_type = "UNAVAILABLE"

# Load review packet if exists
packet_path = Path("data/governance/complete_review_packets") / f"{r['programme_id']}.json"
extracted_criteria = []
mandatory_docs = []

if packet_path.exists():
    try:
        with open(packet_path, "r", encoding="utf-8") as f:
            pkt = json.load(f)
            crits = pkt.get("criteria") or pkt.get("source_evidence") or []
            for c in crits:
                if isinstance(c, dict):
                    extracted_criteria.append({
                        "criterion_id": c.get("criterion_id"),
                        "exact_text": c.get("exact_source_text") or c.get("exact_text") or c.get("evidence"),
                        "fact_key": c.get("fact_key") or c.get("fact"),
                        "operator": c.get("operator"),
                        "expected_value": c.get("expected_value") or c.get("value"),
                    })
            mandatory_docs = pkt.get("mandatory_documents") or []
    except Exception:
        pass

res = {
    "programme_id": r["programme_id"],
    "canonical_name": r["canonical_name"],
    "programme_type": p_type,
    "government_level": gov_level,
    "jurisdiction": jur,
    "authority": r.get("authority"),
    "ministry": r.get("ministry"),
    "department": r.get("department"),
    "state_or_ut": r.get("state_or_ut"),
    "category": r.get("category") or "General",
    "beneficiary_type": r.get("beneficiary_type") or "individual",
    "description": r.get("description"),
    "benefit_summary": r.get("benefit_summary"),
    "application_route": r.get("application_route"),
    "official_url": r.get("official_url"),
    "currentness": r.get("currentness") or "ACTIVE",
    "source_status": r.get("source_status") or "SOURCE_VERIFIED",
    "eligibility_available": bool(r.get("eligibility_available")),
    "eligibility_status": estatus,
    "eligibility_status_label": elig_label,
    "eligibility_banner": banner_msg,
    "banner_type": banner_type,
    "applicability": r.get("applicability") or "CITIZEN",
    "is_certified": is_cert,
    "source_records": json.loads(r.get("source_records") or "[]"),
    "lineage": json.loads(r.get("lineage") or "[]"),
    "created_at": r.get("created_at"),
    "updated_at": r.get("updated_at"),
    "extracted_criteria": extracted_criteria,
    "mandatory_documents": mandatory_docs,
    "documents": [
        {"title": "Official Portal Website", "url": r.get("official_url"), "type": "OFFICIAL_PORTAL"}
    ]
}
print(json.dumps(res))
`
    ];

    const child = spawn(pyExe, args);
    let output = '';
    let error = '';

    child.stdout.on('data', (d) => { output += d; });
    child.stderr.on('data', (d) => { error += d; });

    child.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(error || `Python exited with code ${code}`));
      } else {
        try {
          resolve(JSON.parse(output.trim()));
        } catch (e) {
          reject(e);
        }
      }
    });
  });
}

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  try {
    const upstreamUrl = `${ML_SERVICE_URL}/v1/programmes/${id}`;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 1200);

    const resp = await fetch(upstreamUrl, {
      signal: controller.signal,
      headers: { Accept: 'application/json' },
    });
    clearTimeout(timeout);

    if (resp.ok) {
      const data = await resp.json();
      return NextResponse.json(data);
    }
  } catch {
    // Upstream not available; fall through to direct SQLite execution
  }

  try {
    const data: any = await fetchDetailFallback(id);
    if (data.error) {
      return NextResponse.json({ error: data.error }, { status: 404 });
    }
    return NextResponse.json(data);
  } catch (err: any) {
    console.error('Error in detail route:', err);
    return NextResponse.json(
      { error: 'Failed to retrieve programme', details: err?.message },
      { status: 500 }
    );
  }
}
