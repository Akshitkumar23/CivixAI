import { NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const fileName = searchParams.get('file');

    if (!fileName) {
        return NextResponse.json({ error: 'No file specified' }, { status: 400 });
    }

    try {
        // Try to find the file in common data directories
        const possiblePaths = [
            path.join(process.cwd(), 'data', 'raw', fileName),
            path.join(process.cwd(), 'data', 'processed', fileName),
            path.join(process.cwd(), 'data', 'master', fileName),
            path.join(process.cwd(), 'src', 'lib', fileName), // Check lib as well just in case
        ];

        for (const filePath of possiblePaths) {
            try {
                await fs.access(filePath);
                const data = await fs.readFile(filePath, 'utf-8');
                return NextResponse.json(JSON.parse(data));
            } catch {
                continue;
            }
        }

        // Fallback: If it's a known missing file, return empty array instead of 404
        console.warn(`File not found: ${fileName}. Returning empty array.`);
        return NextResponse.json([]);
    } catch (error) {
        return NextResponse.json({ error: 'Failed to read data' }, { status: 500 });
    }
}
