'use client';

import React from 'react';
import { Message } from '@/lib/types';
import { formatMessageTime } from '@/lib/utils';
import { CheckCheck } from 'lucide-react';

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-slide-up`}
    >
      <div className={isUser ? 'message-bubble-user' : 'message-bubble-bot'}>
        <p className={`text-sm leading-relaxed whitespace-pre-wrap break-words ${isUser ? 'text-gray-100' : 'text-gray-200'}`}>
          {message.content}
        </p>

        <div className="flex items-center justify-end gap-1 mt-1">
          <span className={`text-xs ${isUser ? 'text-gray-400' : 'text-gray-500'}`}>
            {formatMessageTime(message.timestamp)}
          </span>
          {isUser && <CheckCheck className="w-3 h-3 text-blue-400" />}
        </div>
      </div>
    </div>
  );
}
