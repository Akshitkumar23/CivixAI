import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const ML_SERVICE_URL = process.env.ML_API_URL || 'http://127.0.0.1:8000';

async function fetchFromPythonBackend(urlParams: URLSearchParams) {
  return new Promise((resolve, reject) => {
    const pyExe = path.join(process.cwd(), '.venv', 'Scripts', 'python.exe');
    
    // Fallback query script invocation with parameterized query construction
    const args = [
      '-c',
      `
import sys, json, sqlite3
conn = sqlite3.connect('data/civix.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

q = "${urlParams.get('q') || ''}".strip()
jurisdiction = "${urlParams.get('jurisdiction') || ''}".strip()
programme_type = "${urlParams.get('programme_type') || ''}".strip()
state = "${urlParams.get('state') || ''}".strip()
category = "${urlParams.get('category') || ''}".strip()
ministry = "${urlParams.get('ministry') || ''}".strip()
applicability = "${urlParams.get('applicability') || ''}".strip()
eligibility_status = "${urlParams.get('eligibility_status') || ''}".strip()
benefit_type = "${urlParams.get('benefit_type') || ''}".strip()
sort = "${urlParams.get('sort') || 'name_asc'}".strip()

page = int("${urlParams.get('page') || '1'}")
if page < 1:
    page = 1
page_size = int("${urlParams.get('page_size') || '24'}")
if not (1 <= page_size <= 100):
    page_size = 24

query_parts = ["1=1"]
params = []

if q:
    terms = q.split()
    for t in terms:
        query_parts.append("(canonical_name LIKE ? OR aliases LIKE ? OR description LIKE ? OR authority LIKE ? OR ministry LIKE ? OR category LIKE ? OR state_or_ut LIKE ?)")
        kw = f"%{t}%"
        params.extend([kw, kw, kw, kw, kw, kw, kw])

if jurisdiction:
    query_parts.append("jurisdiction = ?")
    params.append(jurisdiction.upper())

if state:
    query_parts.append("state_or_ut LIKE ?")
    params.append(f"%{state}%")

if ministry:
    query_parts.append("ministry LIKE ?")
    params.append(f"%{ministry}%")

if programme_type:
    query_parts.append("programme_type = ?")
    params.append(programme_type.upper())

if category:
    query_parts.append("category LIKE ?")
    params.append(f"%{category}%")

if applicability:
    query_parts.append("applicability = ?")
    params.append(applicability.upper())

if eligibility_status:
    query_parts.append("eligibility_status = ?")
    params.append(eligibility_status.upper())

if benefit_type:
    query_parts.append("benefit_summary LIKE ?")
    params.append(f"%{benefit_type}%")

where_clause = " AND ".join(query_parts)

cur.execute(f"SELECT COUNT(*) FROM programme_discovery WHERE {where_clause}", params)
total = cur.fetchone()[0]

order_clause = "canonical_name ASC"
if sort == "name_desc":
    order_clause = "canonical_name DESC"
elif sort == "recently_verified":
    order_clause = "updated_at DESC"
elif sort == "jurisdiction":
    order_clause = "jurisdiction ASC"
elif sort == "category":
    order_clause = "category ASC"

offset = (page - 1) * page_size
cur.execute(f"SELECT * FROM programme_discovery WHERE {where_clause} ORDER BY {order_clause} LIMIT ? OFFSET ?", params + [page_size, offset])
rows = [dict(r) for r in cur.fetchall()]

# Format items with exact specification badges
items = []
for r in rows:
    p_type = r.get("programme_type") or "SCHEME"
    jur = r.get("jurisdiction") or "CENTRAL"
    gov_level = "Central" if jur == "CENTRAL" else ("UT" if jur == "UT" else "State")
    estatus = r.get("eligibility_status") or "INSUFFICIENT_OFFICIAL_EVIDENCE"
    is_cert = bool(r.get("is_certified"))

    if estatus == "ELIGIBILITY_READY" or is_cert:
        elig_label = "✓ Eligibility verified"
    elif estatus == "ELIGIBILITY_REVIEW":
        elig_label = "Eligibility review pending"
    elif estatus == "INSUFFICIENT_OFFICIAL_EVIDENCE":
        elig_label = "Official evidence unavailable"
    elif estatus in ("INSTITUTIONAL_ONLY", "EMPLOYER_ONLY") or p_type in ("INSTITUTIONAL_PROGRAMME", "EMPLOYER_PROGRAMME"):
        elig_label = "Institution / Employer programme"
    elif estatus == "INFORMATIONAL" or p_type == "INFORMATIONAL_PROGRAMME":
        elig_label = "Informational"
    elif estatus == "SERVICE" or "SERVICE" in p_type:
        elig_label = "Service"
    elif bool(r.get("eligibility_available")):
        elig_label = "Eligibility review pending"
    else:
        elig_label = "Official evidence unavailable"

    desc = r.get("description") or ""
    short_desc = (desc[:220] + "...") if len(desc) > 220 else desc

    items.append({
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
        "description": short_desc,
        "benefit_summary": r.get("benefit_summary"),
        "eligibility_status": estatus,
        "eligibility_status_label": elig_label,
        "applicability": r.get("applicability") or "CITIZEN",
        "source_url": r.get("official_url"),
        "last_verified_at": r.get("updated_at"),
        "certified": is_cert,
    })

# Compute Facets
cur.execute("SELECT programme_type, COUNT(*) FROM programme_discovery GROUP BY programme_type")
ptype_counts = dict(cur.fetchall())

cur.execute("SELECT jurisdiction, COUNT(*) FROM programme_discovery GROUP BY jurisdiction")
jur_counts = dict(cur.fetchall())

cur.execute("SELECT category, COUNT(*) FROM programme_discovery WHERE category IS NOT NULL GROUP BY category ORDER BY COUNT(*) DESC LIMIT 20")
cat_counts = dict(cur.fetchall())

cur.execute("SELECT eligibility_status, COUNT(*) FROM programme_discovery WHERE eligibility_status IS NOT NULL GROUP BY eligibility_status")
elig_status_counts = dict(cur.fetchall())

conn.close()

total_pages = (total + page_size - 1) // page_size if total > 0 else 1

out = {
    "items": items,
    "total": total,
    "page": page,
    "page_size": page_size,
    "total_pages": total_pages,
    "has_next": page < total_pages,
    "has_previous": page > 1,
    "facets": {
        "jurisdiction": jur_counts,
        "categories": cat_counts,
        "eligibility_statuses": elig_status_counts,
        "total_active": total,
        "certified_recommendation_pool": 27
    },
    "source_counts": {
        "canonical_master": 4645,
        "myscheme_portal": 5154,
        "india_gov_schemes": 20,
        "gov_services_portal": 20,
        "dbt_bharat": 20,
        "data_gov_in": 8
    },
    "programme_type_counts": ptype_counts
}
print(json.dumps(out))
`
    ];

    const child = spawn(pyExe, args);
    let output = '';
    let error = '';

    child.stdout.on('data', (data) => { output += data; });
    child.stderr.on('data', (data) => { error += data; });

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

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);

  // 1. Attempt fast HTTP proxy to FastAPI if running
  try {
    const upstreamUrl = `${ML_SERVICE_URL}/v1/programmes?${searchParams.toString()}`;
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

  // 2. Direct SQLite Execution (resilient fallback)
  try {
    const fallbackData = await fetchFromPythonBackend(searchParams);
    return NextResponse.json(fallbackData);
  } catch (err: any) {
    console.error('Error fetching programmes from fallback:', err);
    return NextResponse.json(
      { error: 'Failed to retrieve programmes', details: err?.message },
      { status: 500 }
    );
  }
}
