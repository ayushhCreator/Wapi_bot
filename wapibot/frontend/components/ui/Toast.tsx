'use client';

import React, { useEffect } from 'react';
import { X, Info, CheckCircle, AlertCircle } from 'lucide-react';

export interface ToastProps {
  id: string;
  message: string;
  type?: 'info' | 'success' | 'warning' | 'error';
  duration?: number;
  onClose: (id: string) => void;
}

const Toast: React.FC<ToastProps> = ({
  id,
  message,
  type = 'info',
  duration = 4000,
  onClose,
}) => {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        onClose(id);
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [id, duration, onClose]);

  const icons = {
    info: <Info className="w-5 h-5 text-blue-400" />,
    success: <CheckCircle className="w-5 h-5 text-green-400" />,
    warning: <AlertCircle className="w-5 h-5 text-yellow-400" />,
    error: <AlertCircle className="w-5 h-5 text-red-400" />,
  };

  const borderColors = {
    info: 'border-blue-500/30',
    success: 'border-green-500/30',
    warning: 'border-yellow-500/30',
    error: 'border-red-500/30',
  };

  const bgColors = {
    info: 'bg-blue-500/10',
    success: 'bg-green-500/10',
    warning: 'bg-yellow-500/10',
    error: 'bg-red-500/10',
  };

  return (
    <div
      className={`
        flex items-center gap-3 min-w-[300px] max-w-md
        px-4 py-3 rounded-lg border backdrop-blur-xl
        shadow-lg animate-slide-in-right
        ${bgColors[type]} ${borderColors[type]}
      `}
    >
      <div className="flex-shrink-0">{icons[type]}</div>
      <p className="flex-1 text-sm text-white">{message}</p>
      <button
        onClick={() => onClose(id)}
        className="flex-shrink-0 p-1 hover:bg-white/10 rounded transition-colors"
        aria-label="Close notification"
      >
        <X className="w-4 h-4 text-gray-400" />
      </button>
    </div>
  );
};

export default Toast;
