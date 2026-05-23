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
        <p className="mt-2 text-sm">请点击&ldquo;刷新数据&rdquo;获取最新内容</p>
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
