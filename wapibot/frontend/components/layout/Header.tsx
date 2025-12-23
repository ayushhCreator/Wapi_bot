'use client';

import React, { useEffect, useState } from 'react';
import { useConversationStore } from '@/hooks/useConversations';
import Button from '@/components/ui/Button';
import SettingsPanel from '@/components/settings/SettingsPanel';
import { Settings, Send } from 'lucide-react';

export default function Header() {
  const {
    backendMode,
    setBackendMode,
    selectedOllamaModel,
    setSelectedOllamaModel,
    availableOllamaModels,
  } = useConversationStore();

  const [isLoading, setIsLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // Fetch Ollama models on mount
  useEffect(() => {
    const fetchModels = async () => {
      try {
        setIsLoading(true);
        const response = await fetch('/api/ollama/models');
        if (!response.ok) throw new Error('Failed to fetch models');

        const data = await response.json();
        const modelNames = (data.models || []).map((m: any) => m.name);

        if (modelNames.length > 0) {
          useConversationStore.setState({
            availableOllamaModels: modelNames,
          });

          // Set default model if not already set
          if (
            !selectedOllamaModel ||
            !modelNames.includes(selectedOllamaModel)
          ) {
            const defaultModel = modelNames.includes('gemma3:4b')
              ? 'gemma3:4b'
              : modelNames[0];
            setSelectedOllamaModel(defaultModel);
          }
        }
      } catch (error) {
        console.error('Failed to fetch Ollama models:', error);
      } finally {
        setIsLoading(false);
      }
    };

    if (backendMode === 'ollama') {
      fetchModels();
    }
  }, [backendMode, selectedOllamaModel, setSelectedOllamaModel]);

  return (
    <header className="border-b border-white/10 bg-zinc-900/80 backdrop-blur-xl shadow-lg">
      <div className="flex items-center justify-between px-6 py-4">
        {/* Left: Branding */}
        <div className="flex-shrink-0">
          <h1 className="text-2xl font-bold text-white tracking-tight">WapiBot</h1>
          <p className="text-xs text-gray-500 mt-0.5">WhatsApp Testing Interface</p>
        </div>

        {/* Center: Mode Switcher & Model Selector */}
        <div className="flex items-center gap-3">
          {/* Backend Mode */}
          <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-lg px-4 py-2 hover:bg-white/10 transition-all">
            <label className="text-sm font-medium text-gray-400">Backend:</label>
            <select
              value={backendMode}
              onChange={(e) =>
                setBackendMode(e.target.value as 'ollama' | 'fastapi')
              }
              className="bg-transparent text-white font-medium outline-none text-sm cursor-pointer"
            >
              <option value="ollama" className="bg-zinc-800">Ollama</option>
              <option value="fastapi" className="bg-zinc-800">FastAPI</option>
            </select>
          </div>

          {/* Model Selector (only for Ollama) */}
          {backendMode === 'ollama' && availableOllamaModels.length > 0 && (
            <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-lg px-4 py-2 hover:bg-white/10 transition-all">
              <label className="text-sm font-medium text-gray-400">Model:</label>
              <select
                value={selectedOllamaModel}
                onChange={(e) => setSelectedOllamaModel(e.target.value)}
                className="bg-transparent text-white font-medium outline-none text-sm cursor-pointer max-w-xs"
                disabled={isLoading}
              >
                {availableOllamaModels.map((model) => (
                  <option key={model} value={model} className="bg-zinc-800">
                    {model}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Right: Settings */}
        <div className="flex-shrink-0">
          <Button
            variant="secondary"
            size="icon"
            title="Settings"
            onClick={() => setShowSettings(true)}
            className="hover:bg-white/10"
          >
            <Settings className="w-5 h-5" />
          </Button>
        </div>
      </div>

      {/* Settings Panel Modal (renders via portal to body) */}
      <SettingsPanel isOpen={showSettings} onClose={() => setShowSettings(false)} />
    </header>
  );
}
