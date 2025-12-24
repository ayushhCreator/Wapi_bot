import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import ToastContainer from '@/components/ui/ToastContainer';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'WapiBot - WhatsApp Testing Interface',
  description: 'Test your WhatsApp chatbot with multi-persona simulation',
  viewport: 'width=device-width, initial-scale=1',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="fixed inset-0 bg-gradient-to-br from-black via-zinc-900 to-black">
          {/* Animated background elements */}
          <div className="absolute inset-0 opacity-20">
            <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-white rounded-full blur-[120px] animate-pulse-glow" />
            <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-white rounded-full blur-[120px] animate-pulse-glow animation-delay-1000" />
          </div>
        </div>

        {/* Content */}
        <div className="relative z-10 w-full h-screen">
          {children}
        </div>

        {/* Toast Notifications */}
        <ToastContainer />
      </body>
    </html>
  );
}
