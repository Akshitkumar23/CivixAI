import { NextResponse } from 'next/server';

const ML_SERVICE_URL = process.env.ML_API_URL || 'http://localhost:8000';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const endpoint = body.mode === 'search' ? '/v1/search' : '/v1/rag/query';

    const response = await fetch(`${ML_SERVICE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      return NextResponse.json(
        { error: 'RAG Service error', details: errorText },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (err: any) {
    return NextResponse.json(
      { error: 'Failed to connect to CivixAI RAG Service', details: err.message },
      { status: 502 }
    );
  }
}

export async function GET() {
  try {
    const response = await fetch(`${ML_SERVICE_URL}/v1/rag/schemes`);
    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to fetch verified schemes' },
        { status: response.status }
      );
    }
    const data = await response.json();
    return NextResponse.json(data);
  } catch (err: any) {
    return NextResponse.json(
      { error: 'RAG Service unavailable', details: err.message },
      { status: 502 }
    );
  }
}
