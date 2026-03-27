'use client';

import { Sun, Moon } from 'lucide-react';
import { useTheme } from '@/lib/theme-context';

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="relative w-14 h-8 rounded-full bg-[var(--bg-card)] border border-[var(--border-color)] hover:border-[var(--border-hover)] transition-all duration-300 flex items-center px-1"
      aria-label="Toggle theme"
    >
      <div
        className={`absolute w-6 h-6 rounded-full flex items-center justify-center transition-all duration-300 ${
          theme === 'dark' ? 'translate-x-0' : 'translate-x-6'
        }`}
        style={{
          background: theme === 'dark' 
            ? 'linear-gradient(135deg, #14b8a6 0%, #2dd4bf 100%)'
            : 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)',
        }}
      >
        {theme === 'dark' ? (
          <Moon className="w-3.5 h-3.5 text-white" />
        ) : (
          <Sun className="w-3.5 h-3.5 text-white" />
        )}
      </div>
    </button>
  );
}