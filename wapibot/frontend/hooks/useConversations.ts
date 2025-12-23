'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { AppState, Conversation, Message, BackendMode, BackendSettings } from '@/lib/types';

interface ConversationStore extends AppState {
  // Conversation Actions
  createConversation: (phoneNumber: string, displayName: string) => void;
  deleteConversation: (id: string) => void;
  setActiveConversation: (id: string) => void;

  // Message Actions
  addMessage: (
    conversationId: string,
    messageData: Omit<Message, 'id'>
  ) => void;
  updateMessage: (
    conversationId: string,
    messageId: string,
    updates: Partial<Message>
  ) => void;
  clearMessages: (conversationId: string) => void;

  // Backend Configuration
  setBackendMode: (mode: BackendMode) => void;
  setSelectedOllamaModel: (model: string) => void;
  setAvailableOllamaModels: (models: string[]) => void;

  // UI Actions
  markAsRead: (conversationId: string) => void;

  // Settings Actions
  updateBackendSettings: (settings: Partial<BackendSettings>) => void;
  resetBackendSettings: () => void;
}

export const useConversationStore = create<ConversationStore>()(
  persist(
    (set, get) => ({
      // Initial State
      conversations: [],
      activeConversationId: null,
      backendMode: 'ollama',
      selectedOllamaModel: 'gemma3:4b',
      availableOllamaModels: [],
      backendSettings: {
        ollama: {
          baseUrl: 'http://localhost:11434/v1',
          model: 'gemma3:4b',
          timeout: 30000,
          maxTokens: 512,
          temperature: 0.7,
        },
        fastapi: {
          baseUrl: 'http://localhost:8000',
          endpoint: '/webhook/chat',
          timeout: 30000,
          retries: 3,
        },
      },

      // Create new conversation
      createConversation: (phoneNumber, displayName) => {
        const newConversation: Conversation = {
          id: crypto.randomUUID(),
          phoneNumber,
          displayName,
          messages: [],
          createdAt: new Date(),
          lastMessageAt: new Date(),
          unreadCount: 0,
        };

        set((state) => ({
          conversations: [...state.conversations, newConversation],
          activeConversationId: newConversation.id,
        }));
      },

      // Delete conversation
      deleteConversation: (id) => {
        set((state) => {
          const newConversations = state.conversations.filter((c) => c.id !== id);
          const newActiveId =
            state.activeConversationId === id
              ? newConversations[0]?.id ?? null
              : state.activeConversationId;

          return {
            conversations: newConversations,
            activeConversationId: newActiveId,
          };
        });
      },

      // Set active conversation
      setActiveConversation: (id) => {
        set({ activeConversationId: id });
        get().markAsRead(id);
      },

      // Add message to conversation
      addMessage: (conversationId, messageData) => {
        const message: Message = {
          ...messageData,
          id: crypto.randomUUID(),
        };

        set((state) => ({
          conversations: state.conversations.map((conv) =>
            conv.id === conversationId
              ? {
                  ...conv,
                  messages: [...conv.messages, message],
                  lastMessageAt: new Date(),
                  unreadCount:
                    conv.id !== state.activeConversationId
                      ? conv.unreadCount + 1
                      : 0,
                }
              : conv
          ),
        }));
      },

      // Update message
      updateMessage: (conversationId, messageId, updates) => {
        set((state) => ({
          conversations: state.conversations.map((conv) =>
            conv.id === conversationId
              ? {
                  ...conv,
                  messages: conv.messages.map((msg) =>
                    msg.id === messageId ? { ...msg, ...updates } : msg
                  ),
                }
              : conv
          ),
        }));
      },

      // Clear all messages in conversation
      clearMessages: (conversationId) => {
        set((state) => ({
          conversations: state.conversations.map((conv) =>
            conv.id === conversationId ? { ...conv, messages: [] } : conv
          ),
        }));
      },

      // Set backend mode
      setBackendMode: (mode) => {
        set({ backendMode: mode });
      },

      // Set selected Ollama model
      setSelectedOllamaModel: (model) => {
        set({ selectedOllamaModel: model });
      },

      // Set available Ollama models
      setAvailableOllamaModels: (models) => {
        set({ availableOllamaModels: models });
      },

      // Mark conversation as read
      markAsRead: (conversationId) => {
        set((state) => ({
          conversations: state.conversations.map((conv) =>
            conv.id === conversationId ? { ...conv, unreadCount: 0 } : conv
          ),
        }));
      },

      // Update backend settings
      updateBackendSettings: (newSettings) => {
        set((state) => ({
          backendSettings: {
            ollama: {
              ...state.backendSettings.ollama,
              ...(newSettings.ollama || {}),
            },
            fastapi: {
              ...state.backendSettings.fastapi,
              ...(newSettings.fastapi || {}),
            },
          },
        }));
      },

      // Reset backend settings to defaults
      resetBackendSettings: () => {
        set({
          backendSettings: {
            ollama: {
              baseUrl: 'http://localhost:11434/v1',
              model: 'gemma3:4b',
              timeout: 30000,
              maxTokens: 512,
              temperature: 0.7,
            },
            fastapi: {
              baseUrl: 'http://localhost:8000',
              endpoint: '/webhook/chat',
              timeout: 30000,
              retries: 3,
            },
          },
        });
      },
    }),
    {
      name: 'wapibot-conversations',
      partialize: (state) => ({
        conversations: state.conversations,
        backendMode: state.backendMode,
        selectedOllamaModel: state.selectedOllamaModel,
        availableOllamaModels: state.availableOllamaModels,
        backendSettings: state.backendSettings,
      }),
    }
  )
);
