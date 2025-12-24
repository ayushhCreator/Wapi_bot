/**
 * Application constants
 */

export const APP_NAME = 'WapiBot';
export const APP_VERSION = '0.1.0';

// API Configuration
export const OLLAMA_PREFERRED_MODEL = 'gemma3:4b'; // Preference, not requirement
export const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';
export const FASTAPI_BASE_URL = process.env.NEXT_PUBLIC_FASTAPI_URL || 'http://localhost:8000';

// Timeouts (in ms)
export const API_TIMEOUT = 30000;
export const SOCKET_TIMEOUT = 5000;

// UI Configuration
export const SIDEBAR_WIDTH = 'w-[30%] min-w-[300px] max-w-[400px]';
export const MESSAGE_MAX_WIDTH = 'max-w-[70%]';

// Message Configuration
export const MAX_MESSAGE_LENGTH = 1000;
export const TYPING_INDICATOR_DELAY = 500;

// Backend Modes
export const BACKEND_MODES = {
  OLLAMA: 'ollama',
  FASTAPI: 'fastapi',
} as const;

// Local Storage Keys
export const STORAGE_KEYS = {
  CONVERSATIONS: 'wapibot-conversations',
  THEME: 'wapibot-theme',
  SETTINGS: 'wapibot-settings',
} as const;

// Error Messages
export const ERROR_MESSAGES = {
  OLLAMA_NOT_AVAILABLE: 'Ollama is not available. Make sure it\'s running on localhost:11434',
  FASTAPI_NOT_AVAILABLE: 'FastAPI backend is not available. Make sure it\'s running on localhost:8000',
  INVALID_PHONE_NUMBER: 'Please enter a valid 10-digit Indian phone number',
  INVALID_MESSAGE: 'Message cannot be empty',
  NETWORK_ERROR: 'Network error. Please check your connection',
  UNKNOWN_ERROR: 'An unexpected error occurred',
} as const;

// Success Messages
export const SUCCESS_MESSAGES = {
  CONTACT_CREATED: 'Contact created successfully',
  MESSAGE_SENT: 'Message sent',
  MODE_SWITCHED: 'Backend mode switched',
  MODEL_CHANGED: 'Model changed',
} as const;
