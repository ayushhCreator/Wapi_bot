'use client';

import { useEffect } from 'react';
import { useConversationStore } from '@/hooks/useConversations';
import Header from '@/components/layout/Header';
import Sidebar from '@/components/layout/Sidebar';
import ChatInterface from '@/components/chat/ChatInterface';
import GlassCard from '@/components/ui/GlassCard';

export default function HomePage() {
  const { activeConversationId, conversations } = useConversationStore();

  const activeConversation = conversations.find(
    (c) => c.id === activeConversationId
  );

  return (
    <main className="relative h-full w-full flex flex-col overflow-hidden">
      {/* Header */}
      <Header />

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar - 30% width */}
        <div className="w-[30%] min-w-[300px] max-w-[400px] h-full">
          <Sidebar />
        </div>

        {/* Chat Area - 70% width */}
        <div className="flex-1 h-full flex flex-col">
          {activeConversation ? (
            <ChatInterface conversation={activeConversation} />
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <GlassCard className="p-8 text-center max-w-md">
                <h2 className="text-2xl font-bold mb-2 text-shadow-glow">
                  Welcome to WapiBot
                </h2>
                <p className="text-gray-300 mb-4">
                  Create a new contact from the sidebar to start testing your chatbot.
                </p>
                <p className="text-sm text-gray-400">
                  Pose as multiple contacts to simulate real WhatsApp conversations.
                </p>
              </GlassCard>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
