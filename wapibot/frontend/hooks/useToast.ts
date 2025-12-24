'use client';

import { create } from 'zustand';

export interface Toast {
  id: string;
  message: string;
  type?: 'info' | 'success' | 'warning' | 'error';
  duration?: number;
}

interface ToastStore {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  clearToasts: () => void;
}

export const useToastStore = create<ToastStore>((set) => ({
  toasts: [],

  addToast: (toast) => {
    const id = `toast-${Date.now()}-${Math.random()}`;
    set((state) => ({
      toasts: [...state.toasts, { ...toast, id }],
    }));
  },

  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((toast) => toast.id !== id),
    }));
  },

  clearToasts: () => {
    set({ toasts: [] });
  },
}));

// Convenience hook for common toast actions
export function useToast() {
  const { addToast } = useToastStore();

  return {
    toast: {
      info: (message: string, duration?: number) =>
        addToast({ message, type: 'info', duration }),
      success: (message: string, duration?: number) =>
        addToast({ message, type: 'success', duration }),
      warning: (message: string, duration?: number) =>
        addToast({ message, type: 'warning', duration }),
      error: (message: string, duration?: number) =>
        addToast({ message, type: 'error', duration }),
    },
  };
}
