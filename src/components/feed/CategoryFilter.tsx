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
