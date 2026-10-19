import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const ML_SERVICE_URL = process.env.ML_API_URL || 'http://127.0.0.1:8000';

async function fetchMinistryFallback() {
  return new Promise((resolve, reject) => {
    const pyExe = path.join(process.cwd(), '.venv', 'Scripts', 'python.exe');
    const args = [
      '-c',
      `
import sys, json, sqlite3
conn = sqlite3.connect('data/civix.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
    SELECT ministry, jurisdiction, COUNT(*) as cnt
    FROM programme_discovery
    WHERE ministry IS NOT NULL AND ministry != ''
    GROUP BY ministry, jurisdiction
    ORDER BY cnt DESC
""")
rows = cur.fetchall()

min_dict = {}
for r in rows:
    m_name = r["ministry"]
    jur = r["jurisdiction"]
    cnt = r["cnt"]

    if m_name not in min_dict:
        min_dict[m_name] = {
            "ministry": m_name,
            "programme_count": 0,
            "government_level": "Central" if jur == "CENTRAL" else "State",
        }
    min_dict[m_name]["programme_count"] += cnt

# Top categories per ministry
for m in min_dict:
    cur.execute("SELECT category, COUNT(*) FROM programme_discovery WHERE ministry = ? GROUP BY category ORDER BY COUNT(*) DESC LIMIT 3", (m,))
    min_dict[m]["categories"] = [cr[0] for cr in cur.fetchall() if cr[0]]

conn.close()

out = {
    "total_ministries": len(min_dict),
    "ministries": sorted(list(min_dict.values()), key=lambda x: x["programme_count"], reverse=True)
}
print(json.dumps(out))
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

export async function GET() {
  try {
    const upstreamUrl = `${ML_SERVICE_URL}/v1/programmes/ministry`;
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
    // Fallback to SQLite
  }

  try {
    const fallbackData = await fetchMinistryFallback();
    return NextResponse.json(fallbackData);
  } catch (err: any) {
    return NextResponse.json(
      { error: 'Failed to retrieve ministry breakdown', details: err?.message },
      { status: 500 }
    );
  }
}
