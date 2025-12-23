'use client';

import React, { useState } from 'react';
import { useConversationStore } from '@/hooks/useConversations';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import { Plus, Trash2 } from 'lucide-react';
import GlassCard from '@/components/ui/GlassCard';
import { isValidIndianPhoneNumber, formatPhoneNumber, getInitials } from '@/lib/utils';

export default function Sidebar() {
  const [showNewContact, setShowNewContact] = useState(false);
  const [phoneInput, setPhoneInput] = useState('');
  const [nameInput, setNameInput] = useState('');
  const [phoneError, setPhoneError] = useState('');

  const {
    conversations,
    activeConversationId,
    createConversation,
    deleteConversation,
    setActiveConversation,
  } = useConversationStore();

  const handleCreateContact = () => {
    setPhoneError('');

    if (!phoneInput.trim() || !nameInput.trim()) {
      setPhoneError('Please enter both phone and name');
      return;
    }

    if (!isValidIndianPhoneNumber(phoneInput)) {
      setPhoneError('Invalid phone number. Enter 10-digit number starting with 6-9');
      return;
    }

    // Check if contact already exists
    if (conversations.some((c) => c.phoneNumber === phoneInput.replace(/\D/g, ''))) {
      setPhoneError('This contact already exists');
      return;
    }

    createConversation(phoneInput.replace(/\D/g, ''), nameInput);
    setPhoneInput('');
    setNameInput('');
    setShowNewContact(false);
  };

  return (
    <aside className="h-full flex flex-col border-r border-glass-border glass-card bg-gradient-to-b from-white/[0.08] to-white/[0.03]">
      {/* Header */}
      <div className="p-4 border-b border-glass-border">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-lg font-bold text-shadow-glow">Contacts</h1>
          <Button
            onClick={() => setShowNewContact(!showNewContact)}
            variant="secondary"
            size="icon"
            title="New contact"
          >
            <Plus className="w-5 h-5" />
          </Button>
        </div>
        <p className="text-xs text-gray-400">Simulate multiple WhatsApp contacts</p>
      </div>

      {/* New Contact Form */}
      {showNewContact && (
        <div className="p-4 border-b border-glass-border space-y-3">
          <Input
            type="tel"
            placeholder="Phone (10 digits)"
            value={phoneInput}
            onChange={(e) => {
              setPhoneInput(e.target.value);
              setPhoneError('');
            }}
            error={phoneError || undefined}
          />
          <Input
            type="text"
            placeholder="Display name"
            value={nameInput}
            onChange={(e) => setNameInput(e.target.value)}
          />
          <div className="flex gap-2">
            <Button
              onClick={handleCreateContact}
              variant="primary"
              size="sm"
              className="flex-1"
            >
              Create
            </Button>
            <Button
              onClick={() => {
                setShowNewContact(false);
                setPhoneInput('');
                setNameInput('');
                setPhoneError('');
              }}
              variant="secondary"
              size="sm"
              className="flex-1"
            >
              Cancel
            </Button>
          </div>
        </div>
      )}

      {/* Contact List */}
      <div className="flex-1 overflow-y-auto scrollbar-glass p-3 space-y-2">
        {conversations.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <p className="text-sm">No contacts yet</p>
            <p className="text-xs mt-1">Create one to get started</p>
          </div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => setActiveConversation(conv.id)}
              className={`w-full text-left p-3 rounded-lg transition-all duration-200 group relative cursor-pointer ${
                activeConversationId === conv.id
                  ? 'glass-card border-white/20'
                  : 'hover:bg-white/5'
              }`}
            >
              <div className="flex items-center gap-3">
                {/* Avatar */}
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm ${
                    activeConversationId === conv.id
                      ? 'bg-blue-500/30'
                      : 'bg-white/10'
                  }`}
                >
                  {getInitials(conv.displayName)}
                </div>

                {/* Contact Info */}
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-white truncate">
                    {conv.displayName}
                  </p>
                  <p className="text-xs text-gray-400 truncate">
                    {formatPhoneNumber(conv.phoneNumber)}
                  </p>
                </div>

                {/* Unread Badge */}
                {conv.unreadCount > 0 && (
                  <span className="bg-blue-500 text-white text-xs px-2 py-1 rounded-full">
                    {conv.unreadCount}
                  </span>
                )}

                {/* Delete Button (on hover) */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (
                      confirm(
                        `Delete ${conv.displayName}? This cannot be undone.`
                      )
                    ) {
                      deleteConversation(conv.id);
                    }
                  }}
                  className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-red-500/20 rounded"
                  title="Delete contact"
                >
                  <Trash2 className="w-4 h-4 text-red-400" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-glass-border p-3 text-xs text-gray-400">
        <p>Conversations: {conversations.length}</p>
      </div>
    </aside>
  );
}
