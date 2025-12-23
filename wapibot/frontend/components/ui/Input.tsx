import React from 'react';
import clsx from 'clsx';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, ...props }, ref) => (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-gray-300 mb-2">
          {label}
        </label>
      )}
      <input
        ref={ref}
        className={clsx(
          'glass-input',
          'w-full px-4 py-2',
          'bg-glass-white backdrop-blur-glass',
          'border border-glass-border rounded-lg',
          'text-white placeholder-gray-400',
          'focus:ring-2 focus:ring-white/20 focus:border-white/30',
          'outline-none transition-all duration-200',
          error && 'border-red-500/50 focus:ring-red-500/20',
          className
        )}
        {...props}
      />
      {error && <p className="text-red-400 text-sm mt-1">{error}</p>}
    </div>
  )
);

Input.displayName = 'Input';

export default Input;
