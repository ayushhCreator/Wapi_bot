'use client';

import { useState } from 'react';
import { useConversationStore } from './useConversations';

interface UseOllamaChatResult {
  isLoading: boolean;
  error: string | null;
  sendMessage: (content: string) => Promise<void>;
}

/**
 * Hook for sending messages to Ollama and streaming responses
 */
export function useOllamaChat(conversationId: string): UseOllamaChatResult {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { conversations, addMessage, selectedOllamaModel, backendSettings } =
    useConversationStore();

  const conversation = conversations.find((c) => c.id === conversationId);

  const sendMessage = async (content: string) => {
    if (!conversation || !content.trim()) return;

    // Determine which model to use (prefer selectedOllamaModel, fallback to settings)
    const modelToUse = selectedOllamaModel || backendSettings.ollama.model;

    // Safety check: Ensure a model is available
    if (!modelToUse) {
      const errorMessage = 'No Ollama model available. Please select a model in settings or wait for models to load.';
      setError(errorMessage);
      console.error('[Chat Error]', errorMessage);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      console.log('[Chat] Sending message with model:', modelToUse);

      // Step 1: Add user message to store FIRST
      addMessage(conversationId, {
        role: 'user',
        content,
        timestamp: new Date(),
        phoneNumber: conversation.phoneNumber,
      });

      // Step 2: Prepare messages for API (using current conversation + new user message)
      const previousMessages = conversation.messages.map((msg) => ({
        role: msg.role as 'user' | 'assistant' | 'system',
        content: msg.content,
      }));

      previousMessages.push({
        role: 'user' as const,
        content,
      });

      // Step 3: Call server-side chat API
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: previousMessages,
          model: modelToUse,
          temperature: backendSettings.ollama.temperature,
          numPredict: backendSettings.ollama.maxTokens,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      // Handle Server-Sent Events (SSE) stream
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response stream');
      }

      let fullResponse = '';
      const decoder = new TextDecoder();
      let streamDone = false;

      // Collect all chunks first
      while (!streamDone) {
        const { done, value } = await reader.read();
        if (done) {
          streamDone = true;
          break;
        }

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);

            if (data === '[DONE]') {
              streamDone = true;
              break;
            }

            try {
              const parsed = JSON.parse(data);
              if (parsed.error) {
                throw new Error(parsed.error);
              }
              if (parsed.content) {
                fullResponse += parsed.content;
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }

        if (streamDone) break;
      }

      // Add complete bot message once all chunks are collected
      if (fullResponse) {
        addMessage(conversationId, {
          role: 'assistant',
          content: fullResponse,
          timestamp: new Date(),
          phoneNumber: conversation.phoneNumber,
        });
      }

      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get response from Ollama';
      setError(errorMessage);
      console.error('Chat error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return {
    isLoading,
    error,
    sendMessage,
  };
}
