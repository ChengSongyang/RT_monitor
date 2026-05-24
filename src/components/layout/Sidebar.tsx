"use client";

import { useState } from "react";
import Link from "next/link";
import { Star, Menu, X, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";
import { ThemeSwitcher } from "@/components/ui/ThemeSwitcher";

interface SidebarProps {
  className?: string;
}

export function Sidebar({ className }: SidebarProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        onClick={() => setOpen(true)}
        className="fixed left-3 top-3 z-[60] flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--sidebar)] border border-[var(--border)] text-[var(--foreground)] md:hidden"
        aria-label="打开菜单"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-[55] bg-black/50 md:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed left-0 top-0 z-[60] flex h-full w-[180px] flex-col border-r border-[var(--border)] bg-[var(--sidebar)] py-4 transition-transform duration-200",
          // Mobile: slide in/out
          open ? "translate-x-0" : "-translate-x-full",
          // Desktop: always visible
          "md:translate-x-0",
          className
        )}
      >
        {/* Logo + close button */}
        <div className="mb-8 flex items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 text-xs font-bold text-white">
              RT
            </div>
            <span className="text-sm font-semibold text-[var(--sidebar-foreground)]">
              Monitor
            </span>
          </div>
          <button
            onClick={() => setOpen(false)}
            className="flex h-7 w-7 items-center justify-center rounded text-[var(--muted-foreground)] hover:text-[var(--foreground)] md:hidden"
            aria-label="关闭菜单"
          >
            <X className="h-4 w-4" />
          </button>
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
          <a
            href="http://47.77.216.151:24830"
            target="_blank"
            rel="noopener noreferrer"
            className="mt-1 flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-[var(--sidebar-foreground)] opacity-70 transition-colors hover:bg-white/10 hover:opacity-100"
          >
            <ExternalLink className="h-4 w-4" />
            <span>AI 热点</span>
          </a>
        </nav>

        {/* Bottom: Theme Switcher */}
        <div className="px-3">
          <ThemeSwitcher />
        </div>
      </aside>
    </>
  );
}
