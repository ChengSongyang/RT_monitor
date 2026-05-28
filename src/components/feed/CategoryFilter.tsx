"use client";

import { cn } from "@/lib/utils";

const categories = [
  { key: "all", label: "全部" },
  { key: "paper", label: "论文" },
  { key: "industry_news", label: "行业" },
  { key: "guideline", label: "指南" },
];

interface CategoryFilterProps {
  activeCategory: string;
  onChange: (category: string) => void;
}

export function CategoryFilter({ activeCategory, onChange }: CategoryFilterProps) {
  return (
    <div className="segmented" role="tablist" aria-label="内容分类">
      {categories.map((cat) => {
        return (
          <button
            key={cat.key}
            type="button"
            role="tab"
            aria-selected={activeCategory === cat.key}
            onClick={() => onChange(cat.key)}
            className={cn(
              "seg-item",
              activeCategory === cat.key && "seg-item-active"
            )}
          >
            {cat.label}
          </button>
        );
      })}
    </div>
  );
}
