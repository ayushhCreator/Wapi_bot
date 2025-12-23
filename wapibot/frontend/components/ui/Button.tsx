import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import clsx from 'clsx';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-lg font-medium transition-all duration-200 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed',
  {
    variants: {
      variant: {
        glass:
          'bg-glass-white border border-glass-border hover:bg-glass-hover shadow-glass',
        primary:
          'bg-white/20 border border-white/30 hover:bg-white/30 text-white shadow-lg',
        secondary:
          'bg-transparent border border-white/20 hover:bg-white/5 text-white',
        danger: 'bg-red-500/20 border border-red-500/30 hover:bg-red-500/30 text-red-300',
      },
      size: {
        sm: 'px-3 py-1.5 text-sm',
        md: 'px-4 py-2 text-base',
        lg: 'px-6 py-3 text-lg',
        icon: 'w-10 h-10 p-2',
      },
    },
    defaultVariants: {
      variant: 'glass',
      size: 'md',
    },
  }
);

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button
      ref={ref}
      className={clsx(buttonVariants({ variant, size }), className)}
      {...props}
    />
  )
);

Button.displayName = 'Button';

export default Button;
