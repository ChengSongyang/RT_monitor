"use client";

import Link from "next/link";
import { Star } from "lucide-react";
import { cn } from "@/lib/utils";
import { ThemeSwitcher } from "@/components/ui/ThemeSwitcher";

interface SidebarProps {
  className?: string;
}

export function Sidebar({ className }: SidebarProps) {
  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-50 flex h-full w-[180px] flex-col border-r border-[var(--border)] bg-[var(--sidebar)] py-4",
        className
      )}
    >
      {/* Logo */}
      <div className="mb-8 px-4">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 text-xs font-bold text-white">
            RT
          </div>
          <span className="text-sm font-semibold text-[var(--sidebar-foreground)]">
            Monitor
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3">
        <Link
          href="/"
          className="flex items-center gap-3 rounded-lg bg-white/10 px-3 py-2 text-sm font-medium text-cyan-400 transition-colors"
        >
          <Star className="h-4 w-4" />
          <span>精选</span>
        </Link>
      </nav>

      {/* Bottom: Theme Switcher */}
      <div className="px-3">
        <ThemeSwitcher />
      </div>
    </aside>
  );
}
