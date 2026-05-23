# RT Monitor UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the RT Monitor frontend to match AIHOT's visual quality — wide sidebar, rich news cards, theme switching, pagination, and component-based architecture.

**Architecture:** Decompose the monolithic `page.tsx` (378 lines) into focused components under `src/components/`. Add a ThemeProvider context for dark/light/system switching via CSS variables. Backend pagination via `page` + `limit` params. Each task produces a working, committed increment.

**Tech Stack:** Next.js 16 (App Router), React 19, Tailwind CSS v4, Lucide React, TypeScript strict

---

## File Map

```
Create:
  src/types/index.ts                              — Shared TypeScript interfaces
  src/providers/ThemeProvider.tsx                  — React context for theme state + localStorage
  src/components/ui/Badge.tsx                     — Reusable badge component
  src/components/ui/ThemeSwitcher.tsx              — Dark/System/Light radio group
  src/components/ui/ImageGallery.tsx              — Thumbnail grid + lightbox modal
  src/components/layout/Sidebar.tsx               — Fixed sidebar with nav + theme switcher
  src/components/feed/NewsCard.tsx                — Individual news item card
  src/components/feed/DateGroup.tsx               — Date section header + items
  src/components/feed/FeedList.tsx                — Feed with date groups + empty state
  src/components/feed/CategoryFilter.tsx          — Horizontal tab pills
  src/components/feed/SearchBar.tsx               — Search input + button
  src/components/feed/Pagination.tsx              — Page navigation

Modify:
  src/app/globals.css                             — Add oklch color tokens for light/dark
  src/app/layout.tsx                              — Wrap children in ThemeProvider, remove hardcoded "dark"
  src/app/page.tsx                                — Rewrite to compose new components
  src/app/api/items/route.ts                      — Add page param, compute totalPages
  api_server.py                                   — Add page-based pagination, new item fields
```

---

## Task 1: TypeScript Types

**Files:**
- Create: `src/types/index.ts`

- [ ] **Step 1: Create the shared types file**

```ts
export interface NewsItem {
  id: string;
  title: string;
  content: string;
  summary: string;
  source: string;
  source_user: string;
  source_verified: boolean;
  source_verified_reason: string;
  date: string;
  timestamp: number;
  url: string;
  image_urls: string[];
  hot_score: number;
  recommendation_score: number;
  content_type: string;
  tags: string[];
  category: string;
  pdf_url?: string;
  html_url?: string;
  journal?: string;
  is_featured: boolean;
  quoted_text?: string;
  quoted_author?: string;
  recommendation_reason?: string;
}

export interface PaginatedResponse {
  items: NewsItem[];
  total: number;
  page: number;
  totalPages: number;
  limit: number;
}

export type ThemeMode = "dark" | "system" | "light";

export interface Category {
  key: string;
  label: string;
  icon: string; // lucide icon name
}
```

- [ ] **Step 2: Commit**

```bash
git add src/types/index.ts
git commit -m "feat: add shared TypeScript types for NewsItem, pagination, and theme"
```

---

## Task 2: Theme System — CSS Variables

**Files:**
- Modify: `src/app/globals.css`

- [ ] **Step 1: Rewrite globals.css with oklch color tokens**

Replace the entire contents of `src/app/globals.css` with:

```css
@import "tailwindcss";

@custom-variant dark (&:is(.dark *));

:root {
  --background: oklch(1 0 0);
  --foreground: oklch(0.15 0 0);
  --card: oklch(0.98 0 0);
  --card-foreground: oklch(0.15 0 0);
  --border: oklch(0.9 0 0);
  --muted: oklch(0.95 0 0);
  --muted-foreground: oklch(0.5 0 0);
  --accent: oklch(0.7 0.15 190);
  --accent-foreground: oklch(1 0 0);
  --sidebar: oklch(0.97 0 0);
  --sidebar-foreground: oklch(0.15 0 0);
}

.dark {
  --background: oklch(0.1 0 0);
  --foreground: oklch(1 0 0);
  --card: oklch(0.13 0 0);
  --card-foreground: oklch(1 0 0);
  --border: oklch(0.2 0 0);
  --muted: oklch(0.15 0 0);
  --muted-foreground: oklch(0.5 0 0);
  --accent: oklch(0.7 0.15 190);
  --accent-foreground: oklch(1 0 0);
  --sidebar: oklch(0.12 0 0);
  --sidebar-foreground: oklch(0.85 0 0);
}

body {
  background: var(--background);
  color: var(--foreground);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    "Helvetica Neue", Arial, "Noto Sans", sans-serif,
    "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: var(--muted-foreground);
}

/* Line clamping */
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
```

- [ ] **Step 2: Commit**

```bash
git add src/app/globals.css
git commit -m "feat: add oklch color tokens for light/dark theme system"
```

---

## Task 3: Theme System — ThemeProvider

**Files:**
- Create: `src/providers/ThemeProvider.tsx`
- Modify: `src/app/layout.tsx`

- [ ] **Step 1: Create ThemeProvider**

```tsx
"use client";

import { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import type { ThemeMode } from "@/types";

interface ThemeContextType {
  theme: ThemeMode;
  setTheme: (theme: ThemeMode) => void;
  resolvedTheme: "dark" | "light";
}

const ThemeContext = createContext<ThemeContextType>({
  theme: "dark",
  setTheme: () => {},
  resolvedTheme: "dark",
});

export function useTheme() {
  return useContext(ThemeContext);
}

function getSystemTheme(): "dark" | "light" {
  if (typeof window === "undefined") return "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function resolveTheme(mode: ThemeMode): "dark" | "light" {
  return mode === "system" ? getSystemTheme() : mode;
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemeMode>("dark");
  const [resolvedTheme, setResolvedTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    const stored = localStorage.getItem("rt-monitor-theme") as ThemeMode | null;
    if (stored && ["dark", "system", "light"].includes(stored)) {
      setThemeState(stored);
      setResolvedTheme(resolveTheme(stored));
    }
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove("dark", "light");
    root.classList.add(resolvedTheme);
  }, [resolvedTheme]);

  useEffect(() => {
    if (theme !== "system") return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => setResolvedTheme(getSystemTheme());
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, [theme]);

  const setTheme = (mode: ThemeMode) => {
    setThemeState(mode);
    setResolvedTheme(resolveTheme(mode));
    localStorage.setItem("rt-monitor-theme", mode);
  };

  return (
    <ThemeContext.Provider value={{ theme, setTheme, resolvedTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
```

- [ ] **Step 2: Update layout.tsx to use ThemeProvider**

Replace `src/app/layout.tsx` with:

```tsx
import type { Metadata } from "next";
import "./globals.css";
import { ThemeProvider } from "@/providers/ThemeProvider";

export const metadata: Metadata = {
  title: "RT Monitor - 放射治疗领域监控",
  description: "监控放射治疗领域的最新新闻、论文和行业动态",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className="antialiased">
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
```

- [ ] **Step 3: Verify it compiles**

Run: `npm run typecheck`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/providers/ThemeProvider.tsx src/app/layout.tsx
git commit -m "feat: add ThemeProvider with dark/light/system support"
```

---

## Task 4: ThemeSwitcher Component

**Files:**
- Create: `src/components/ui/ThemeSwitcher.tsx`

- [ ] **Step 1: Create ThemeSwitcher**

```tsx
"use client";

import { Moon, Monitor, Sun } from "lucide-react";
import { useTheme } from "@/providers/ThemeProvider";
import { cn } from "@/lib/utils";
import type { ThemeMode } from "@/types";

const themes: { mode: ThemeMode; icon: typeof Moon; label: string }[] = [
  { mode: "dark", icon: Moon, label: "深色" },
  { mode: "system", icon: Monitor, label: "跟随系统" },
  { mode: "light", icon: Sun, label: "浅色" },
];

export function ThemeSwitcher() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="flex items-center gap-1 rounded-lg bg-white/5 p-1">
      {themes.map(({ mode, icon: Icon, label }) => (
        <button
          key={mode}
          onClick={() => setTheme(mode)}
          title={label}
          className={cn(
            "flex h-7 w-7 items-center justify-center rounded-md transition-colors",
            theme === mode
              ? "bg-white/15 text-white"
              : "text-gray-400 hover:text-white hover:bg-white/10"
          )}
        >
          <Icon className="h-4 w-4" />
        </button>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add src/components/ui/ThemeSwitcher.tsx
git commit -m "feat: add ThemeSwitcher component"
```

---

## Task 5: Badge Component

**Files:**
- Create: `src/components/ui/Badge.tsx`

- [ ] **Step 1: Create Badge component**

```tsx
import { cn } from "@/lib/utils";

const variantStyles: Record<string, string> = {
  default: "bg-white/10 text-gray-300 border-white/10",
  paper: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  industry_news: "bg-green-500/20 text-green-400 border-green-500/30",
  guideline: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  research: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  conference: "bg-pink-500/20 text-pink-400 border-pink-500/30",
  featured: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  score: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
};

interface BadgeProps {
  children: React.ReactNode;
  variant?: string;
  className?: string;
}

export function Badge({ children, variant = "default", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-medium",
        variantStyles[variant] || variantStyles.default,
        className
      )}
    >
      {children}
    </span>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add src/components/ui/Badge.tsx
git commit -m "feat: add reusable Badge component with color variants"
```

---

## Task 6: Sidebar Component

**Files:**
- Create: `src/components/layout/Sidebar.tsx`

- [ ] **Step 1: Create Sidebar**

```tsx
"use client";

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
        <a
          href="/"
          className="flex items-center gap-3 rounded-lg bg-white/10 px-3 py-2 text-sm font-medium text-cyan-400 transition-colors"
        >
          <Star className="h-4 w-4" />
          <span>精选</span>
        </a>
      </nav>

      {/* Bottom: Theme Switcher */}
      <div className="px-3">
        <ThemeSwitcher />
      </div>
    </aside>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add src/components/layout/Sidebar.tsx
git commit -m "feat: add Sidebar component with navigation and theme switcher"
```

---

## Task 7: CategoryFilter Component

**Files:**
- Create: `src/components/feed/CategoryFilter.tsx`

- [ ] **Step 1: Create CategoryFilter**

```tsx
"use client";

import { FileText, BookOpen, Activity, TrendingUp, Newspaper } from "lucide-react";
import { cn } from "@/lib/utils";

const categories = [
  { key: "all", label: "全部", icon: FileText },
  { key: "paper", label: "论文", icon: BookOpen },
  { key: "industry_news", label: "行业动态", icon: Activity },
  { key: "guideline", label: "指南共识", icon: FileText },
  { key: "research", label: "研究进展", icon: TrendingUp },
  { key: "conference", label: "学术会议", icon: Newspaper },
];

interface CategoryFilterProps {
  activeCategory: string;
  onChange: (category: string) => void;
}

export function CategoryFilter({ activeCategory, onChange }: CategoryFilterProps) {
  return (
    <div className="flex items-center gap-2 overflow-x-auto pb-2">
      {categories.map((cat) => {
        const Icon = cat.icon;
        return (
          <button
            key={cat.key}
            onClick={() => onChange(cat.key)}
            className={cn(
              "flex items-center gap-1.5 whitespace-nowrap rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
              activeCategory === cat.key
                ? "bg-white/15 text-white"
                : "text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-white/10"
            )}
          >
            <Icon className="h-3.5 w-3.5" />
            {cat.label}
          </button>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add src/components/feed/CategoryFilter.tsx
git commit -m "feat: add CategoryFilter component"
```

---

## Task 8: SearchBar Component

**Files:**
- Create: `src/components/feed/SearchBar.tsx`

- [ ] **Step 1: Create SearchBar**

```tsx
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
```

- [ ] **Step 2: Commit**

```bash
git add src/components/feed/SearchBar.tsx
git commit -m "feat: add SearchBar component"
```

---

## Task 9: Pagination Component

**Files:**
- Create: `src/components/feed/Pagination.tsx`

- [ ] **Step 1: Create Pagination**

```tsx
"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;

  const pages: (number | "...")[] = [];
  if (totalPages <= 7) {
    for (let i = 1; i <= totalPages; i++) pages.push(i);
  } else {
    pages.push(1);
    if (page > 3) pages.push("...");
    for (
      let i = Math.max(2, page - 1);
      i <= Math.min(totalPages - 1, page + 1);
      i++
    ) {
      pages.push(i);
    }
    if (page < totalPages - 2) pages.push("...");
    pages.push(totalPages);
  }

  return (
    <div className="flex items-center justify-center gap-1 pt-6 pb-2">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--muted-foreground)] hover:bg-white/10 hover:text-[var(--foreground)] disabled:opacity-30 disabled:pointer-events-none transition-colors"
      >
        <ChevronLeft className="h-4 w-4" />
      </button>

      {pages.map((p, i) =>
        p === "..." ? (
          <span key={`dots-${i}`} className="px-1 text-[var(--muted-foreground)]">
            ...
          </span>
        ) : (
          <button
            key={p}
            onClick={() => onPageChange(p)}
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-lg text-sm transition-colors",
              p === page
                ? "bg-white/15 text-white font-medium"
                : "text-[var(--muted-foreground)] hover:bg-white/10 hover:text-[var(--foreground)]"
            )}
          >
            {p}
          </button>
        )
      )}

      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--muted-foreground)] hover:bg-white/10 hover:text-[var(--foreground)] disabled:opacity-30 disabled:pointer-events-none transition-colors"
      >
        <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add src/components/feed/Pagination.tsx
git commit -m "feat: add Pagination component with ellipsis"
```

---

## Task 10: ImageGallery Component

**Files:**
- Create: `src/components/ui/ImageGallery.tsx`

- [ ] **Step 1: Create ImageGallery with lightbox**

```tsx
"use client";

import { useState } from "react";
import { X, ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface ImageGalleryProps {
  images: string[];
}

export function ImageGallery({ images }: ImageGalleryProps) {
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);

  if (!images || images.length === 0) return null;

  const openLightbox = (index: number) => {
    setActiveIndex(index);
    setLightboxOpen(true);
  };

  const navigate = (dir: -1 | 1) => {
    setActiveIndex((prev) => (prev + dir + images.length) % images.length);
  };

  return (
    <>
      <div className="flex gap-2 flex-wrap">
        {images.slice(0, 4).map((src, i) => (
          <button
            key={i}
            onClick={() => openLightbox(i)}
            className="group relative overflow-hidden rounded-lg border border-[var(--border)]"
          >
            <img
              src={src}
              alt={`图片 ${i + 1}`}
              className="h-20 w-20 object-cover transition-transform group-hover:scale-105"
            />
            {i === 3 && images.length > 4 && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/60 text-xs text-white">
                +{images.length - 4}
              </div>
            )}
          </button>
        ))}
      </div>

      {lightboxOpen && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80"
          onClick={() => setLightboxOpen(false)}
        >
          <button
            onClick={() => setLightboxOpen(false)}
            className="absolute right-4 top-4 text-white/80 hover:text-white"
          >
            <X className="h-6 w-6" />
          </button>

          {images.length > 1 && (
            <button
              onClick={(e) => { e.stopPropagation(); navigate(-1); }}
              className="absolute left-4 text-white/80 hover:text-white"
            >
              <ChevronLeft className="h-8 w-8" />
            </button>
          )}

          <img
            src={images[activeIndex]}
            alt={`图片 ${activeIndex + 1}`}
            className="max-h-[80vh] max-w-[80vw] rounded-lg object-contain"
            onClick={(e) => e.stopPropagation()}
          />

          {images.length > 1 && (
            <button
              onClick={(e) => { e.stopPropagation(); navigate(1); }}
              className="absolute right-4 text-white/80 hover:text-white"
            >
              <ChevronRight className="h-8 w-8" />
            </button>
          )}

          {images.length > 1 && (
            <div className="absolute bottom-4 text-sm text-white/60">
              {activeIndex + 1} / {images.length}
            </div>
          )}
        </div>
      )}
    </>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add src/components/ui/ImageGallery.tsx
git commit -m "feat: add ImageGallery with lightbox modal"
```

---

## Task 11: NewsCard Component

**Files:**
- Create: `src/components/feed/NewsCard.tsx`

- [ ] **Step 1: Create NewsCard**

```tsx
import { Badge } from "@/components/ui/Badge";
import { ImageGallery } from "@/components/ui/ImageGallery";
import type { NewsItem } from "@/types";

const contentTypeLabels: Record<string, string> = {
  paper: "论文",
  industry_news: "行业动态",
  guideline: "指南共识",
  research: "研究进展",
  conference: "学术会议",
  case_report: "病例报告",
  discussion: "讨论",
};

function formatTime(timestamp: number): string {
  try {
    const date = new Date(timestamp * 1000);
    return `${date.getHours().toString().padStart(2, "0")}:${date.getMinutes().toString().padStart(2, "0")}`;
  } catch {
    return "";
  }
}

interface NewsCardProps {
  item: NewsItem;
}

export function NewsCard({ item }: NewsCardProps) {
  return (
    <article className="group border-b border-[var(--border)] py-4">
      {/* Top row: time + source + badges */}
      <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-[var(--muted-foreground)]">
        <span>{formatTime(item.timestamp)}</span>
        <span className="font-medium text-[var(--foreground)]">{item.source}</span>
        {item.source_user && <span>{item.source_user}</span>}
        {item.source_verified && (
          <Badge variant="default">{item.source_verified_reason || "已认证"}</Badge>
        )}
        {item.is_featured && <Badge variant="featured">精选</Badge>}
      </div>

      {/* Title */}
      <a
        href={item.url}
        target="_blank"
        rel="noopener noreferrer"
        className="block"
      >
        <h3 className="mb-2 text-[15px] font-medium text-[var(--foreground)] leading-snug group-hover:text-[var(--accent)] transition-colors line-clamp-2">
          {item.title}
        </h3>
      </a>

      {/* Summary */}
      {item.summary && (
        <p className="mb-3 text-sm text-[var(--muted-foreground)] leading-relaxed line-clamp-3">
          {item.summary}
        </p>
      )}

      {/* Quoted text */}
      {item.quoted_text && (
        <blockquote className="mb-3 border-l-2 border-[var(--accent)]/40 pl-3 text-sm text-[var(--muted-foreground)] italic">
          {item.quoted_author && (
            <span className="font-medium not-italic text-[var(--foreground)]">
              {item.quoted_author}:
            </span>{" "}
          )}
          {item.quoted_text}
        </blockquote>
      )}

      {/* Image gallery */}
      {item.image_urls && item.image_urls.length > 0 && (
        <div className="mb-3">
          <ImageGallery images={item.image_urls} />
        </div>
      )}

      {/* Bottom row: tags + score */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <Badge variant={item.content_type}>
          {contentTypeLabels[item.content_type] || item.content_type}
        </Badge>
        {item.tags.slice(0, 3).map((tag, i) => (
          <Badge key={i}>{tag}</Badge>
        ))}
        {item.journal && (
          <span className="text-[10px] text-[var(--muted-foreground)]">
            {item.journal}
          </span>
        )}
        {item.recommendation_score > 0 && (
          <Badge variant="score" className="ml-auto font-semibold">
            {item.recommendation_score}
          </Badge>
        )}
      </div>

      {/* Recommendation reason */}
      {item.recommendation_reason && (
        <p className="mt-2 text-xs text-[var(--muted-foreground)]">
          推荐理由：{item.recommendation_reason}
        </p>
      )}
    </article>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add src/components/feed/NewsCard.tsx
git commit -m "feat: add NewsCard component with badges, quoted text, gallery"
```

---

## Task 12: DateGroup and FeedList Components

**Files:**
- Create: `src/components/feed/DateGroup.tsx`
- Create: `src/components/feed/FeedList.tsx`

- [ ] **Step 1: Create DateGroup**

```tsx
import { NewsCard } from "./NewsCard";
import type { NewsItem } from "@/types";

function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today.getTime() - 86400000);
    const target = new Date(date.getFullYear(), date.getMonth(), date.getDate());

    if (target.getTime() === today.getTime()) return "今天";
    if (target.getTime() === yesterday.getTime()) return "昨天";
    return `${date.getMonth() + 1}月${date.getDate()}日`;
  } catch {
    return dateStr;
  }
}

interface DateGroupProps {
  dateKey: string;
  items: NewsItem[];
}

export function DateGroup({ dateKey, items }: DateGroupProps) {
  return (
    <div>
      <h2 className="mb-1 px-1 text-sm font-medium text-[var(--muted-foreground)]">
        {formatDate(dateKey)}
      </h2>
      <div>
        {items.map((item) => (
          <NewsCard key={item.id} item={item} />
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create FeedList**

```tsx
import { FileText } from "lucide-react";
import { DateGroup } from "./DateGroup";
import type { NewsItem } from "@/types";

interface FeedListProps {
  items: NewsItem[];
  loading: boolean;
}

function groupByDate(items: NewsItem[]): Record<string, NewsItem[]> {
  const groups: Record<string, NewsItem[]> = {};
  items.forEach((item) => {
    const key = item.date.substring(0, 10);
    if (!groups[key]) groups[key] = [];
    groups[key].push(item);
  });
  return groups;
}

export function FeedList({ items, loading }: FeedListProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-[var(--accent)] border-t-transparent" />
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="py-16 text-center text-[var(--muted-foreground)]">
        <FileText className="mx-auto mb-4 h-12 w-12 opacity-50" />
        <p className="text-lg">暂无数据</p>
        <p className="mt-2 text-sm">请点击"刷新数据"获取最新内容</p>
      </div>
    );
  }

  const groups = groupByDate(items);
  const sortedDates = Object.keys(groups).sort((a, b) => b.localeCompare(a));

  return (
    <div className="space-y-6">
      {sortedDates.map((dateKey) => (
        <DateGroup key={dateKey} dateKey={dateKey} items={groups[dateKey]} />
      ))}
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add src/components/feed/DateGroup.tsx src/components/feed/FeedList.tsx
git commit -m "feat: add DateGroup and FeedList components"
```

---

## Task 13: Rewrite page.tsx

**Files:**
- Modify: `src/app/page.tsx`

- [ ] **Step 1: Rewrite page.tsx**

Replace the entire contents of `src/app/page.tsx` with:

```tsx
"use client";

import { useState, useEffect, useCallback } from "react";
import { RefreshCw } from "lucide-react";
import { Sidebar } from "@/components/layout/Sidebar";
import { CategoryFilter } from "@/components/feed/CategoryFilter";
import { SearchBar } from "@/components/feed/SearchBar";
import { FeedList } from "@/components/feed/FeedList";
import { Pagination } from "@/components/feed/Pagination";
import type { NewsItem, PaginatedResponse } from "@/types";

const ITEMS_PER_PAGE = 20;

export default function HomePage() {
  const [items, setItems] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  const fetchItems = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (activeCategory !== "all") params.append("category", activeCategory);
      if (searchQuery) params.append("search", searchQuery);
      params.append("page", String(page));
      params.append("limit", String(ITEMS_PER_PAGE));

      const res = await fetch(`/api/items?${params.toString()}`);
      const data: PaginatedResponse = await res.json();
      setItems(data.items || []);
      setTotalPages(data.totalPages || 1);
      setTotal(data.total || 0);
    } catch (err) {
      console.error("Failed to fetch items:", err);
    } finally {
      setLoading(false);
    }
  }, [activeCategory, searchQuery, page]);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await fetch("/api/refresh", { method: "POST" });
      await fetchItems();
    } catch (err) {
      console.error("Failed to refresh:", err);
    } finally {
      setRefreshing(false);
    }
  };

  const handleCategoryChange = (cat: string) => {
    setActiveCategory(cat);
    setPage(1);
  };

  const handleSearch = () => {
    setSearchQuery(searchInput);
    setPage(1);
  };

  return (
    <div className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <Sidebar />

      <main className="ml-[180px] p-6">
        <div className="mx-auto max-w-[800px]">
          {/* Header */}
          <div className="mb-6">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold">精选</h1>
                <p className="mt-1 text-sm text-[var(--muted-foreground)]">
                  放射治疗领域的热点新闻与论文
                </p>
              </div>
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="flex items-center gap-2 rounded-lg bg-white/10 px-4 py-2 text-sm text-[var(--foreground)] hover:bg-white/20 transition-colors disabled:opacity-50"
              >
                <RefreshCw
                  className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`}
                />
                刷新数据
              </button>
            </div>

            <CategoryFilter
              activeCategory={activeCategory}
              onChange={handleCategoryChange}
            />

            <div className="mt-4">
              <SearchBar
                value={searchInput}
                onChange={setSearchInput}
                onSearch={handleSearch}
              />
            </div>
          </div>

          {/* Feed */}
          <FeedList items={items} loading={loading} />

          {/* Pagination */}
          <Pagination
            page={page}
            totalPages={totalPages}
            onPageChange={setPage}
          />

          {/* Total count */}
          {total > 0 && (
            <p className="py-4 text-center text-xs text-[var(--muted-foreground)]">
              共 {total} 条
            </p>
          )}
        </div>
      </main>
    </div>
  );
}
```

- [ ] **Step 2: Verify compilation**

Run: `npm run typecheck`
Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add src/app/page.tsx
git commit -m "feat: rewrite page.tsx to compose new component architecture"
```

---

## Task 14: Backend Pagination — api_server.py

**Files:**
- Modify: `api_server.py`

- [ ] **Step 1: Update get_combined_data to support page-based pagination**

In `api_server.py`, replace the `get_combined_data` function (starting around line 139) with:

```python
def get_combined_data(category=None, source=None, search=None, limit=20, page=1):
    """获取合并的新闻和论文数据"""
    papers = load_papers()
    news = load_news()
    
    # 转换论文为统一格式
    formatted_papers = []
    for paper in papers:
        formatted_papers.append({
            'id': paper.get('id', ''),
            'title': paper.get('title', ''),
            'content': paper.get('abstract', ''),
            'summary': paper.get('abstract', '')[:200] + '...' if len(paper.get('abstract', '')) > 200 else paper.get('abstract', ''),
            'source': paper.get('source', ''),
            'source_user': paper.get('authors', ''),
            'source_verified': True,
            'source_verified_reason': '学术论文',
            'date': paper.get('date', ''),
            'timestamp': parse_date_to_timestamp(paper.get('date', '')),
            'url': paper.get('url', ''),
            'image_urls': paper.get('image_urls', []),
            'hot_score': 70,
            'recommendation_score': paper.get('recommendation_score', 70),
            'content_type': 'paper',
            'tags': ['论文', '学术研究'] + paper.get('categories', '').split(', ')[:3],
            'category': 'paper',
            'pdf_url': paper.get('pdf_url', ''),
            'html_url': paper.get('html_url', ''),
            'journal': paper.get('journal', ''),
            'is_featured': paper.get('is_featured', False),
            'quoted_text': paper.get('quoted_text', ''),
            'quoted_author': paper.get('quoted_author', ''),
            'recommendation_reason': paper.get('recommendation_reason', ''),
        })
    
    # 合并数据
    combined = formatted_papers + news
    
    # 按时间排序
    combined.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    
    # 应用筛选
    if category:
        combined = [item for item in combined if item.get('category') == category]
    
    if source:
        combined = [item for item in combined if item.get('source') == source]
    
    if search:
        search_lower = search.lower()
        combined = [item for item in combined if 
                   search_lower in item.get('title', '').lower() or 
                   search_lower in item.get('content', '').lower() or
                   search_lower in item.get('summary', '').lower()]
    
    # 分页
    total = len(combined)
    total_pages = max(1, (total + limit - 1) // limit)
    page = max(1, min(page, total_pages))
    start = (page - 1) * limit
    items = combined[start:start + limit]
    
    return {
        'items': items,
        'total': total,
        'page': page,
        'totalPages': total_pages,
        'limit': limit,
    }
```

- [ ] **Step 2: Update the API handler to use page param**

In the `do_GET` method, replace the `/api/items` block with:

```python
        if path == '/api/items':
            category = query.get('category', [None])[0]
            source = query.get('source', [None])[0]
            search = query.get('search', [None])[0]
            limit = int(query.get('limit', [20])[0])
            page = int(query.get('page', [1])[0])
            
            data = get_combined_data(category, source, search, limit, page)
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
```

- [ ] **Step 3: Commit**

```bash
git add api_server.py
git commit -m "feat: add page-based pagination and new item fields to backend"
```

---

## Task 15: Next.js API Route Update

**Files:**
- Modify: `src/app/api/items/route.ts`

- [ ] **Step 1: Update items route to pass page param**

Replace the entire contents of `src/app/api/items/route.ts` with:

```ts
import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL = process.env.API_BASE_URL || "http://localhost:8001";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const category = searchParams.get("category");
  const source = searchParams.get("source");
  const search = searchParams.get("search");
  const limit = searchParams.get("limit") || "20";
  const page = searchParams.get("page") || "1";

  try {
    const params = new URLSearchParams();
    if (category) params.append("category", category);
    if (source) params.append("source", source);
    if (search) params.append("search", search);
    params.append("limit", limit);
    params.append("page", page);

    const response = await fetch(`${API_BASE_URL}/api/items?${params.toString()}`, {
      cache: "no-store",
    });
    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error("Failed to fetch items:", error);
    return NextResponse.json(
      { items: [], total: 0, page: 1, totalPages: 1, limit: 20, error: "Failed to fetch items" },
      { status: 500 }
    );
  }
}
```

- [ ] **Step 2: Verify full build**

Run: `npm run check`
Expected: PASS (lint + typecheck + build)

- [ ] **Step 3: Commit**

```bash
git add src/app/api/items/route.ts
git commit -m "feat: update items API route to support page-based pagination"
```

---

## Task 16: Verify Full Application

- [ ] **Step 1: Run typecheck**

Run: `npm run typecheck`
Expected: PASS

- [ ] **Step 2: Run lint**

Run: `npm run lint`
Expected: PASS

- [ ] **Step 3: Run full check**

Run: `npm run check`
Expected: PASS (lint + typecheck + build)

- [ ] **Step 4: Commit any fixes if needed**

```bash
git add -A
git commit -m "fix: resolve lint/type issues from UI redesign"
```
