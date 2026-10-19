import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const ML_SERVICE_URL = process.env.ML_API_URL || 'http://127.0.0.1:8000';

async function fetchFiltersFallback() {
  return new Promise((resolve, reject) => {
    const pyExe = path.join(process.cwd(), '.venv', 'Scripts', 'python.exe');
    const args = [
      '-c',
      `
import sys, json, sqlite3
conn = sqlite3.connect('data/civix.db')
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM programme_discovery")
total = cur.fetchone()[0]

cur.execute("SELECT category, COUNT(*) FROM programme_discovery WHERE category IS NOT NULL GROUP BY category ORDER BY COUNT(*) DESC")
categories = dict(cur.fetchall())

cur.execute("SELECT state_or_ut, COUNT(*) FROM programme_discovery WHERE state_or_ut IS NOT NULL GROUP BY state_or_ut ORDER BY COUNT(*) DESC")
states_and_uts = dict(cur.fetchall())

cur.execute("SELECT jurisdiction, COUNT(*) FROM programme_discovery GROUP BY jurisdiction")
jurisdictions = dict(cur.fetchall())

cur.execute("SELECT ministry, COUNT(*) FROM programme_discovery WHERE ministry IS NOT NULL GROUP BY ministry ORDER BY COUNT(*) DESC LIMIT 50")
ministries = dict(cur.fetchall())

cur.execute("SELECT programme_type, COUNT(*) FROM programme_discovery GROUP BY programme_type ORDER BY COUNT(*) DESC")
programme_types = dict(cur.fetchall())

cur.execute("SELECT applicability, COUNT(*) FROM programme_discovery WHERE applicability IS NOT NULL GROUP BY applicability")
applicabilities = dict(cur.fetchall())

cur.execute("SELECT eligibility_status, COUNT(*) FROM programme_discovery WHERE eligibility_status IS NOT NULL GROUP BY eligibility_status")
eligibility_statuses = dict(cur.fetchall())

conn.close()

out = {
    "total_programmes": total,
    "certified_recommendation_pool": 27,
    "categories": categories,
    "states_and_uts": states_and_uts,
    "jurisdictions": jurisdictions,
    "ministries": ministries,
    "programme_types": programme_types,
    "applicabilities": applicabilities,
    "eligibility_statuses": eligibility_statuses,
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

export async function GET() {
  try {
    const upstreamUrl = `${ML_SERVICE_URL}/v1/programmes/filters`;
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
    const fallbackData = await fetchFiltersFallback();
    return NextResponse.json(fallbackData);
  } catch (err: any) {
    return NextResponse.json(
      { error: 'Failed to retrieve filters', details: err?.message },
      { status: 500 }
    );
  }
}
