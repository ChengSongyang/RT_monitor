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
