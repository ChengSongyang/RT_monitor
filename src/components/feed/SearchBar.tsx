"use client";

import { Search } from "lucide-react";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSearch: () => void;
}

export function SearchBar({ value, onChange, onSearch }: SearchBarProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch();
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--muted-foreground)]" />
        <input
          type="text"
          placeholder="搜索标题/摘要..."
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full rounded-lg border border-[var(--border)] bg-[var(--card)] py-2.5 pl-10 pr-4 text-sm text-[var(--foreground)] placeholder-[var(--muted-foreground)] outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)]/50 transition-colors"
        />
      </div>
      <button
        type="submit"
        className="rounded-lg bg-white/10 px-4 py-2.5 text-sm font-medium text-[var(--foreground)] hover:bg-white/20 transition-colors"
      >
        搜索
      </button>
    </form>
  );
}
