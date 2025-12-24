/**
 * Utility functions for WapiBot
 */

/**
 * Validate Indian phone number format (10 digits, starts with 6-9)
 */
export function isValidIndianPhoneNumber(phone: string): boolean {
  const cleaned = phone.replace(/\D/g, '');
  return /^[6-9]\d{9}$/.test(cleaned);
}

/**
 * Format phone number to Indian format
 */
export function formatPhoneNumber(phone: string): string {
  const cleaned = phone.replace(/\D/g, '');
  if (cleaned.length !== 10) return phone;
  return `+91 ${cleaned.slice(0, 5)} ${cleaned.slice(5)}`;
}

/**
 * Get initials from name for avatar
 */
export function getInitials(name: string): string {
  return name
    .split(' ')
    .map((word) => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

/**
 * Format date to readable format
 */
export function formatMessageTime(date: Date | string): string {
  const now = new Date();
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const diffMs = now.getTime() - dateObj.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'now';
  if (diffMins < 60) return `${diffMins}m`;
  if (diffHours < 24) return `${diffHours}h`;
  if (diffDays < 7) return `${diffDays}d`;

  return dateObj.toLocaleDateString('en-IN', {
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Truncate text with ellipsis
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

/**
 * Get color based on contact ID (for avatar)
 */
export function getColorFromId(id: string): string {
  const colors = [
    'bg-blue-500',
    'bg-purple-500',
    'bg-pink-500',
    'bg-green-500',
    'bg-yellow-500',
    'bg-indigo-500',
    'bg-cyan-500',
    'bg-orange-500',
  ];

  let hash = 0;
  for (let i = 0; i < id.length; i++) {
    hash = id.charCodeAt(i) + ((hash << 5) - hash);
  }

  return colors[Math.abs(hash) % colors.length];
}

/**
 * Debounce function
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;

  return function (...args: Parameters<T>) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

/**
 * Parse ISO date string
 */
export function parseDate(dateString: string | Date): Date {
  if (dateString instanceof Date) return dateString;
  return new Date(dateString);
}

/**
 * Intelligently selects the best available Ollama model
 * Priority: savedPreference > preferredModel > firstAvailable
 *
 * @param availableModels - List of models available from ollama list
 * @param savedPreference - User's previously saved model choice (if any)
 * @param preferredModel - Default preferred model (gemma3:4b by default)
 * @returns The best available model, or null if no models available
 */
export function selectBestAvailableModel(
  availableModels: string[],
  savedPreference?: string | null,
  preferredModel: string = 'gemma3:4b'
): string | null {
  // Priority 1: User's saved preference (if still available)
  if (savedPreference && availableModels.includes(savedPreference)) {
    console.log('[Model Selection] Using saved preference:', savedPreference);
    return savedPreference;
  }

  // Priority 2: Preferred model (gemma3:4b by default)
  if (availableModels.includes(preferredModel)) {
    console.log('[Model Selection] Using preferred model:', preferredModel);
    return preferredModel;
  }

  // Priority 3: First available model
  if (availableModels.length > 0) {
    console.log('[Model Selection] Using first available model:', availableModels[0]);
    return availableModels[0];
  }

  // No models available
  console.warn('[Model Selection] No Ollama models available');
  return null;
}
