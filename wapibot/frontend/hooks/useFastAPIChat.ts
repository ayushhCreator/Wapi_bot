'use client';

import { useState } from 'react';
import { useConversationStore } from './useConversations';

interface UseFastAPIChatResult {
  isLoading: boolean;
  error: string | null;
  sendMessage: (content: string) => Promise<void>;
}

/**
 * Hook for sending messages to FastAPI backend using WAPI-like payload format
 * This enables testing the same workflow as production WAPI from the frontend
 */
export function useFastAPIChat(conversationId: string): UseFastAPIChatResult {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { conversations, addMessage, backendSettings } = useConversationStore();
  const conversation = conversations.find((c) => c.id === conversationId);

  const sendMessage = async (content: string) => {
    if (!conversation || !content.trim()) return;

    try {
      setIsLoading(true);
      setError(null);

      console.log('[FastAPI Chat] Sending message:', content);

      // Add user message to store first
      addMessage(conversationId, {
        role: 'user',
        content,
        timestamp: new Date(),
        phoneNumber: conversation.phoneNumber,
      });

      // Build conversation history
      const previousMessages = conversation.messages.map((msg) => ({
        role: msg.role as 'user' | 'assistant',
        content: msg.content,
      }));

      // Prepare WAPI-like payload for testing
      const nameParts = conversation.displayName.split(' ');
      const payload = {
        contact: {
          phone_number: conversation.phoneNumber,
          first_name: nameParts[0] || '',
          last_name: nameParts.slice(1).join(' ') || '',
        },
        message: {
          body: content,
          message_id: `frontend_${Date.now()}`,
        },
        history: previousMessages.slice(0, -1), // Exclude current message
      };

      console.log('[FastAPI Chat] Sending WAPI-like payload:', payload);

      // Call backend
      const baseUrl = backendSettings.fastapi.baseUrl;
      const response = await fetch(`${baseUrl}/api/v1/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `API error: ${response.status}`);
      }

      const data = await response.json();
      console.log('[FastAPI Chat] Response:', data);

      // Add bot response
      if (data.message) {
        addMessage(conversationId, {
          role: 'assistant',
          content: data.message,
          timestamp: new Date(),
          phoneNumber: conversation.phoneNumber,
          metadata: {
            extracted_data: data.extracted_data,
            completeness: data.completeness,
            should_confirm: data.should_confirm,
            service_request_id: data.service_request_id,
          },
        });
      }

      setError(null);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to connect to backend';
      setError(errorMessage);
      console.error('[FastAPI Chat] Error:', err);

      // Optionally: Add error message to chat
      addMessage(conversationId, {
        role: 'assistant',
        content: `Error: ${errorMessage}`,
        timestamp: new Date(),
        phoneNumber: conversation.phoneNumber,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return { isLoading, error, sendMessage };
}
