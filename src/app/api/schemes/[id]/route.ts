import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const ML_SERVICE_URL = process.env.ML_API_URL || 'http://127.0.0.1:8000';

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const { searchParams } = new URL(request.url);
    const sessionId = searchParams.get('session_id');

    let backendUrl = `${ML_SERVICE_URL}/v1/schemes/${encodeURIComponent(id)}`;
    if (sessionId) {
      backendUrl += `?session_id=${encodeURIComponent(sessionId)}`;
    }

    const res = await fetch(backendUrl, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      cache: 'no-store'
    });

    if (!res.ok) {
      const errText = await res.text();
      console.warn(`[GET /api/schemes/${id}] backend returned ${res.status}: ${errText}`);
      return NextResponse.json({ error: 'Scheme not found' }, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error: any) {
    console.error(`[GET /api/schemes/[id]] Error:`, error);
    return NextResponse.json(
      { error: 'Failed to fetch scheme details from backend service' },
      { status: 500 }
    );
  }
}
