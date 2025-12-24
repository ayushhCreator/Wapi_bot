'use client';

import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useConversationStore } from '@/hooks/useConversations';
import GlassCard from '@/components/ui/GlassCard';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import { X, RotateCcw, Save, RefreshCw } from 'lucide-react';

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SettingsPanel({ isOpen, onClose }: SettingsPanelProps) {
  const { backendSettings, availableOllamaModels, updateBackendSettings, resetBackendSettings } =
    useConversationStore();

  // Local state for form editing
  const [ollamaBaseUrl, setOllamaBaseUrl] = useState(backendSettings.ollama.baseUrl);
  const [ollamaModel, setOllamaModel] = useState(backendSettings.ollama.model);
  const [ollamaTimeout, setOllamaTimeout] = useState(backendSettings.ollama.timeout);
  const [ollamaMaxTokens, setOllamaMaxTokens] = useState(backendSettings.ollama.maxTokens);
  const [ollamaTemperature, setOllamaTemperature] = useState(
    backendSettings.ollama.temperature
  );

  const [fastapiBaseUrl, setFastapiBaseUrl] = useState(backendSettings.fastapi.baseUrl);
  const [fastapiEndpoint, setFastapiEndpoint] = useState(backendSettings.fastapi.endpoint);
  const [fastapiTimeout, setFastapiTimeout] = useState(backendSettings.fastapi.timeout);
  const [fastapiRetries, setFastapiRetries] = useState(backendSettings.fastapi.retries);

  const [saveSuccess, setSaveSuccess] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshSuccess, setRefreshSuccess] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleSaveSettings = () => {
    // Validate that selected Ollama model is available
    if (ollamaModel && !availableOllamaModels.includes(ollamaModel)) {
      console.error(`Selected model "${ollamaModel}" is not available`);
      alert(`Error: Model "${ollamaModel}" is not available. Please select a valid model or refresh the models list.`);
      return;
    }

    updateBackendSettings({
      ollama: {
        baseUrl: ollamaBaseUrl,
        model: ollamaModel,
        timeout: ollamaTimeout,
        maxTokens: ollamaMaxTokens,
        temperature: ollamaTemperature,
      },
      fastapi: {
        baseUrl: fastapiBaseUrl,
        endpoint: fastapiEndpoint,
        timeout: fastapiTimeout,
        retries: fastapiRetries,
      },
    });

    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2000);
  };

  const handleRefreshModels = async () => {
    try {
      setIsRefreshing(true);
      const response = await fetch('/api/ollama/models');

      if (!response.ok) {
        throw new Error(`Failed to fetch models: ${response.statusText}`);
      }

      const data = await response.json();
      const modelNames = (data.models || []).map((m: any) => m.name);

      useConversationStore.setState({
        availableOllamaModels: modelNames,
      });

      setRefreshSuccess(true);
      setTimeout(() => setRefreshSuccess(false), 2000);

      console.log('[Settings] Models refreshed:', modelNames.length);
    } catch (error) {
      console.error('[Settings] Failed to refresh models:', error);
      alert('Failed to refresh models. Make sure Ollama is running.');
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleResetSettings = () => {
    if (confirm('Reset all settings to defaults?')) {
      resetBackendSettings();
      setOllamaBaseUrl(backendSettings.ollama.baseUrl);
      setOllamaModel(backendSettings.ollama.model);
      setOllamaTimeout(backendSettings.ollama.timeout);
      setOllamaMaxTokens(backendSettings.ollama.maxTokens);
      setOllamaTemperature(backendSettings.ollama.temperature);
      setFastapiBaseUrl(backendSettings.fastapi.baseUrl);
      setFastapiEndpoint(backendSettings.fastapi.endpoint);
      setFastapiTimeout(backendSettings.fastapi.timeout);
      setFastapiRetries(backendSettings.fastapi.retries);
    }
  };

  if (!isOpen || !mounted) return null;

  const modalContent = (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <GlassCard className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-glass-border sticky top-0 bg-glass-white/50 backdrop-blur-glass">
          <h2 className="text-2xl font-bold text-shadow-glow">Backend Settings</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-white/10 rounded-lg transition-colors"
            title="Close settings"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-8">
          {/* Success Messages */}
          {saveSuccess && (
            <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-3 text-green-300 text-sm">
              ✓ Settings saved successfully
            </div>
          )}
          {refreshSuccess && (
            <div className="bg-blue-500/20 border border-blue-500/50 rounded-lg p-3 text-blue-300 text-sm">
              ✓ Models refreshed successfully ({availableOllamaModels.length} model{availableOllamaModels.length !== 1 ? 's' : ''} found)
            </div>
          )}

          {/* OLLAMA SECTION */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">Ollama Configuration</h3>
            <p className="text-sm text-gray-400">
              Local LLM server for streaming responses
            </p>

            <Input
              label="Base URL"
              type="url"
              value={ollamaBaseUrl}
              onChange={(e) => setOllamaBaseUrl(e.target.value)}
              placeholder="http://localhost:11434/v1"
            />

            {/* Model Selector */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-300">
                  Select Model
                </label>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleRefreshModels}
                  disabled={isRefreshing}
                  className="flex items-center gap-1.5 text-xs"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
                  {isRefreshing ? 'Refreshing...' : 'Refresh Models'}
                </Button>
              </div>
              <select
                value={ollamaModel || ''}
                onChange={(e) => setOllamaModel(e.target.value)}
                className="w-full glass-input px-4 py-2 rounded-lg outline-none text-white bg-white/5"
              >
                {availableOllamaModels.length === 0 ? (
                  <option value="" className="bg-black text-white">No models available - check Ollama connection</option>
                ) : (
                  <>
                    {availableOllamaModels.map((model) => (
                      <option key={model} value={model} className="bg-black text-white">
                        {model}
                      </option>
                    ))}
                  </>
                )}
              </select>
              <p className="text-xs text-gray-400 mt-1">
                {availableOllamaModels.length === 0
                  ? 'Run "ollama list" to see available models, or click "Refresh Models" above'
                  : `${availableOllamaModels.length} model(s) available`}
              </p>
            </div>

            <Input
              label="Max Tokens"
              type="number"
              value={ollamaMaxTokens}
              onChange={(e) => setOllamaMaxTokens(Number(e.target.value))}
              min="1"
              max="4096"
            />

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Temperature (0.0 - 2.0)
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={ollamaTemperature}
                onChange={(e) => setOllamaTemperature(Number(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-gray-400 mt-1">
                Lower = more focused, Higher = more creative (Current: {ollamaTemperature})
              </p>
            </div>

            <Input
              label="Request Timeout (ms)"
              type="number"
              value={ollamaTimeout}
              onChange={(e) => setOllamaTimeout(Number(e.target.value))}
              min="1000"
              max="300000"
            />
          </div>

          {/* FASTAPI SECTION */}
          <div className="space-y-4 border-t border-glass-border pt-8">
            <h3 className="text-lg font-semibold text-white">FastAPI Configuration</h3>
            <p className="text-sm text-gray-400">
              Your custom WhatsApp bot backend server
            </p>

            <Input
              label="Base URL"
              type="url"
              value={fastapiBaseUrl}
              onChange={(e) => setFastapiBaseUrl(e.target.value)}
              placeholder="http://localhost:8000"
            />

            <Input
              label="Webhook Endpoint"
              type="text"
              value={fastapiEndpoint}
              onChange={(e) => setFastapiEndpoint(e.target.value)}
              placeholder="/webhook/chat"
            />

            <p className="text-xs text-gray-400">
              Full URL will be: <code className="bg-black/40 text-green-300 px-2 py-1 rounded font-mono text-xs">{fastapiBaseUrl}{fastapiEndpoint}</code>
            </p>

            <Input
              label="Request Timeout (ms)"
              type="number"
              value={fastapiTimeout}
              onChange={(e) => setFastapiTimeout(Number(e.target.value))}
              min="1000"
              max="300000"
            />

            <Input
              label="Retry Attempts"
              type="number"
              value={fastapiRetries}
              onChange={(e) => setFastapiRetries(Number(e.target.value))}
              min="1"
              max="10"
            />
          </div>

          {/* INSTRUCTIONS */}
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 space-y-2">
            <p className="text-sm font-medium text-blue-300">Setup Instructions</p>
            <ul className="text-xs text-blue-200 space-y-1">
              <li>
                📝 <strong>Ollama:</strong> Run <code className="bg-black/30 px-1 rounded">ollama serve</code> and use default settings
              </li>
              <li>
                🚀 <strong>FastAPI:</strong> Start your bot backend and set the correct base URL and endpoint
              </li>
              <li>
                🔄 <strong>Toggle:</strong> Switch between backends in the header
              </li>
              <li>
                💾 <strong>Save:</strong> Click Save to persist these settings
              </li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-glass-border p-6 flex gap-2 justify-end sticky bottom-0 bg-glass-white/50 backdrop-blur-glass">
          <Button
            onClick={handleResetSettings}
            variant="secondary"
            className="flex items-center gap-2"
          >
            <RotateCcw className="w-4 h-4" />
            Reset
          </Button>
          <Button onClick={onClose} variant="secondary">
            Cancel
          </Button>
          <Button onClick={handleSaveSettings} variant="primary" className="flex items-center gap-2">
            <Save className="w-4 h-4" />
            Save Settings
          </Button>
        </div>
      </GlassCard>
    </div>
  );

  return createPortal(modalContent, document.body);
}
