import { NextResponse } from 'next/server';

export const runtime = 'nodejs';

export async function GET() {
  try {
    const ollamaBaseUrl =
      process.env.OLLAMA_BASE_URL || 'http://localhost:11434';

    // Remove /v1 from the end if present, as tags endpoint is at the base
    const baseUrl = ollamaBaseUrl.replace(/\/v1\/?$/, '');

    const response = await fetch(`${baseUrl}/api/tags`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Ollama returned ${response.status}`);
    }

    const data = (await response.json()) as { models?: any[] };

    return NextResponse.json({
      models: data.models || [],
      success: true,
    });
  } catch (error) {
    console.error('Failed to fetch Ollama models:', error);
    return NextResponse.json(
      {
        models: [],
        error:
          error instanceof Error
            ? error.message
            : 'Failed to fetch models from Ollama',
      },
      { status: 503 }
    );
  }
}
