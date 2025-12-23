'use client';

import React, { useRef, useEffect, useState } from 'react';
import { Conversation, Message } from '@/lib/types';
import { useConversationStore } from '@/hooks/useConversations';
import { useOllamaChat } from '@/hooks/useOllamaChat';
import GlassCard from '@/components/ui/GlassCard';
import Button from '@/components/ui/Button';
import { Send, Loader2, AlertCircle } from 'lucide-react';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';

interface ChatInterfaceProps {
  conversation: Conversation;
}

export default function ChatInterface({ conversation }: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [input, setInput] = useState('');
  const { backendMode } = useConversationStore();
  const { isLoading, error, sendMessage } = useOllamaChat(conversation.id);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation.messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim() || isLoading) return;

    const message = input;
    setInput('');

    try {
      await sendMessage(message);
    } catch (err) {
      console.error('Failed to send message:', err);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Message Area */}
      <div className="flex-1 overflow-y-auto scrollbar-glass p-4 space-y-3">
        {conversation.messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <GlassCard className="p-6 text-center">
              <p className="text-gray-300">No messages yet</p>
              <p className="text-sm text-gray-400 mt-2">
                Start chatting with {conversation.displayName}
              </p>
            </GlassCard>
          </div>
        ) : (
          <>
            {conversation.messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {isLoading && <TypingIndicator />}
            {error && (
              <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3 text-red-300 text-sm flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                {error}
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-glass-border p-4 bg-glass-white/20 backdrop-blur-glass">
        <form onSubmit={handleSendMessage} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            className="flex-1 glass-input px-4 py-2 rounded-lg outline-none"
            disabled={isLoading}
          />
          <Button
            type="submit"
            disabled={!input.trim() || isLoading}
            variant="primary"
            size="icon"
            title="Send message"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}
