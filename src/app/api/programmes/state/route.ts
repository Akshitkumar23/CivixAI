import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const ML_SERVICE_URL = process.env.ML_API_URL || 'http://127.0.0.1:8000';

async function fetchStateFallback() {
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
    SELECT state_or_ut, jurisdiction, COUNT(*) as cnt
    FROM programme_discovery
    WHERE state_or_ut IS NOT NULL AND state_or_ut != ''
    GROUP BY state_or_ut, jurisdiction
    ORDER BY cnt DESC
""")
rows = cur.fetchall()

states_dict = {}
for r in rows:
    st_name = r["state_or_ut"]
    jur = r["jurisdiction"]
    cnt = r["cnt"]

    if st_name not in states_dict:
        states_dict[st_name] = {
            "state_name": st_name,
            "total": 0,
            "central_contributing": 0,
            "state_ut_dedicated": 0,
            "jurisdiction": jur,
        }
    states_dict[st_name]["total"] += cnt
    if jur == "CENTRAL":
        states_dict[st_name]["central_contributing"] += cnt
    else:
        states_dict[st_name]["state_ut_dedicated"] += cnt

# Get top categories for each state
for st in states_dict:
    cur.execute("SELECT category, COUNT(*) FROM programme_discovery WHERE state_or_ut = ? GROUP BY category ORDER BY COUNT(*) DESC LIMIT 3", (st,))
    states_dict[st]["top_categories"] = [cr[0] for cr in cur.fetchall() if cr[0]]

conn.close()

out = {
    "total_states_represented": len(states_dict),
    "states": sorted(list(states_dict.values()), key=lambda x: x["total"], reverse=True)
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
    const upstreamUrl = `${ML_SERVICE_URL}/v1/programmes/state`;
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
    const fallbackData = await fetchStateFallback();
    return NextResponse.json(fallbackData);
  } catch (err: any) {
    return NextResponse.json(
      { error: 'Failed to retrieve state breakdown', details: err?.message },
      { status: 500 }
    );
  }
}
