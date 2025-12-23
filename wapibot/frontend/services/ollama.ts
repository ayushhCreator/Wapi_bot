/**
 * Ollama service - Proper implementation using official Ollama library
 */

import { Ollama } from 'ollama';
import { OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL } from '@/lib/constants';

// Initialize Ollama client
let ollamaClient: Ollama | null = null;

/**
 * Get or create Ollama client instance
 */
export function getOllamaClient(): Ollama {
  if (!ollamaClient) {
    ollamaClient = new Ollama({
      host: OLLAMA_BASE_URL,
    });
  }
  return ollamaClient;
}

/**
 * Check if Ollama is available
 */
export async function checkOllamaAvailability(): Promise<boolean> {
  try {
    const client = getOllamaClient();
    await client.list();
    return true;
  } catch (error) {
    console.error('Ollama unavailable:', error);
    return false;
  }
}

/**
 * Get list of available models from Ollama
 */
export async function getAvailableModels(): Promise<string[]> {
  try {
    const client = getOllamaClient();
    const response = await client.list();
    return (response.models || []).map((model) => model.name);
  } catch (error) {
    console.error('Failed to fetch models:', error);
    return [];
  }
}

/**
 * Send a chat message to Ollama and get streaming response
 */
export async function* streamChatMessage(
  messages: Array<{ role: 'user' | 'assistant' | 'system'; content: string }>,
  model: string = OLLAMA_DEFAULT_MODEL,
  options?: {
    temperature?: number;
    top_p?: number;
    top_k?: number;
    num_predict?: number; // Max tokens
  }
): AsyncGenerator<string, void, unknown> {
  try {
    const client = getOllamaClient();

    const response = await client.chat({
      model,
      messages,
      stream: true,
      ...(options && {
        options: {
          temperature: options.temperature,
          top_p: options.top_p,
          top_k: options.top_k,
          num_predict: options.num_predict,
        },
      }),
    });

    // Iterate through streaming response
    for await (const chunk of response) {
      if (chunk.message?.content) {
        yield chunk.message.content;
      }
    }
  } catch (error) {
    console.error('Chat error:', error);
    throw new Error(`Failed to get response from Ollama: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Send a chat message and get complete response (non-streaming)
 */
export async function chatMessage(
  messages: Array<{ role: 'user' | 'assistant' | 'system'; content: string }>,
  model: string = OLLAMA_DEFAULT_MODEL,
  options?: {
    temperature?: number;
    top_p?: number;
    top_k?: number;
    num_predict?: number;
  }
): Promise<string> {
  try {
    const client = getOllamaClient();

    const response = await client.chat({
      model,
      messages,
      stream: false,
      ...(options && {
        options: {
          temperature: options.temperature,
          top_p: options.top_p,
          top_k: options.top_k,
          num_predict: options.num_predict,
        },
      }),
    });

    return response.message.content;
  } catch (error) {
    console.error('Chat error:', error);
    throw new Error(`Failed to get response from Ollama: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

/**
 * Generate text from a prompt
 */
export async function* streamGenerateText(
  prompt: string,
  model: string = OLLAMA_DEFAULT_MODEL,
  options?: {
    temperature?: number;
    top_p?: number;
    top_k?: number;
    num_predict?: number;
  }
): AsyncGenerator<string, void, unknown> {
  try {
    const client = getOllamaClient();

    const response = await client.generate({
      model,
      prompt,
      stream: true,
      ...(options && {
        options: {
          temperature: options.temperature,
          top_p: options.top_p,
          top_k: options.top_k,
          num_predict: options.num_predict,
        },
      }),
    });

    for await (const chunk of response) {
      if (chunk.response) {
        yield chunk.response;
      }
    }
  } catch (error) {
    console.error('Generate error:', error);
    throw new Error(`Failed to generate text: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}
