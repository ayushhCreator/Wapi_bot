/**
 * Chat API Route - Handles Ollama communication server-side
 */

import { NextRequest, NextResponse } from 'next/server';
import { Ollama } from 'ollama';

const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';

export const runtime = 'nodejs';

/**
 * POST /api/chat
 * Send a chat message to Ollama and stream the response
 *
 * Body:
 * {
 *   messages: Array<{ role: string; content: string }>,
 *   model: string,
 *   temperature?: number,
 *   numPredict?: number (max tokens)
 * }
 */
export async function POST(request: NextRequest) {
  try {
    const { messages, model, temperature = 0.7, numPredict = 512 } = await request.json();

    if (!messages || !Array.isArray(messages)) {
      return NextResponse.json({ error: 'Invalid messages format' }, { status: 400 });
    }

    if (!model) {
      return NextResponse.json({ error: 'Model not specified' }, { status: 400 });
    }

    // Initialize Ollama client
    const ollama = new Ollama({
      host: OLLAMA_BASE_URL,
    });

    // Create a ReadableStream for streaming response
    const stream = new ReadableStream({
      async start(controller) {
        try {
          // Get streaming response from Ollama
          const response = await ollama.chat({
            model,
            messages: messages.map((msg: any) => ({
              role: msg.role,
              content: msg.content,
            })),
            stream: true,
            options: {
              temperature,
              num_predict: numPredict,
            },
          });

          // Stream chunks back to client
          for await (const chunk of response) {
            if (chunk.message?.content) {
              // Send JSON-formatted chunk
              controller.enqueue(
                new TextEncoder().encode(`data: ${JSON.stringify({ content: chunk.message.content })}\n\n`)
              );
            }
          }

          // Send completion signal
          controller.enqueue(new TextEncoder().encode('data: [DONE]\n\n'));
          controller.close();
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          controller.enqueue(
            new TextEncoder().encode(`data: ${JSON.stringify({ error: errorMessage })}\n\n`)
          );
          controller.close();
        }
      },
    });

    // Return streaming response
    return new NextResponse(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        Connection: 'keep-alive',
      },
    });
  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Internal server error' },
      { status: 500 }
    );
  }
}
