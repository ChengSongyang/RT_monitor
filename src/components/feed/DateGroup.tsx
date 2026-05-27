import { ChevronDown } from "lucide-react";
import { NewsCard } from "./NewsCard";
import type { NewsItem } from "@/types";

function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr);
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
    <section className="timeline-day">
      <div className="timeline-day-head">
        <div className="timeline-date">{formatDate(dateKey)}</div>
        <span className="timeline-day-toggle" aria-hidden="true">
          <ChevronDown className="h-3.5 w-3.5" />
        </span>
      </div>
      <div className="timeline-day-items">
        {items.map((item) => (
          <NewsCard key={item.id} item={item} />
        ))}
      </div>
    </section>
  );
}
