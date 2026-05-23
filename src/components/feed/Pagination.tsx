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
