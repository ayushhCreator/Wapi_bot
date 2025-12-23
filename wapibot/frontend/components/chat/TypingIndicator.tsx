'use client';

import React from 'react';

export default function TypingIndicator() {
  return (
    <div className="flex justify-start animate-slide-up">
      <div className="message-bubble-bot flex items-center gap-1">
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce animation-delay-500" />
        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce animation-delay-1000" />
      </div>
    </div>
  );
}
