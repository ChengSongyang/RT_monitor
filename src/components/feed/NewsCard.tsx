import { Badge } from "@/components/ui/Badge";
import { ImageGallery } from "@/components/ui/ImageGallery";
import { FileText, ExternalLink } from "lucide-react";
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
    <article className="group relative rounded-lg border border-[var(--border)] bg-[var(--card)] p-4 transition-all hover:border-[var(--accent)]/30 hover:shadow-lg hover:shadow-[var(--accent)]/5">
      {/* Top row: time + source */}
      <div className="mb-3 flex items-center justify-between text-xs text-[var(--muted-foreground)]">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[var(--accent)]">
            {formatTime(item.timestamp)}
          </span>
          <span className="font-medium text-[var(--foreground)]">
            {item.source}
          </span>
          {item.source_verified && (
            <span className="rounded-full bg-[var(--accent)]/10 px-2 py-0.5 text-[10px] text-[var(--accent)]">
              ✓ 已认证
            </span>
          )}
        </div>
        {item.is_featured && (
          <span className="rounded-full bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium text-amber-400">
            精选
          </span>
        )}
      </div>

      {/* Title */}
      <a
        href={item.url}
        target="_blank"
        rel="noopener noreferrer"
        className="block"
      >
        <h3 className="mb-2 text-[15px] font-semibold leading-snug text-[var(--foreground)] group-hover:text-[var(--accent)] transition-colors line-clamp-2">
          {item.title}
          <ExternalLink className="ml-1 inline h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
        </h3>
      </a>

      {/* Summary */}
      {item.summary && (
        <p className="mb-3 text-sm leading-relaxed text-[var(--muted-foreground)] line-clamp-3">
          {item.summary}
        </p>
      )}

      {/* Quoted text */}
      {item.quoted_text && (
        <blockquote className="mb-3 border-l-2 border-[var(--accent)]/40 pl-3 text-sm text-[var(--muted-foreground)] italic">
          {item.quoted_author && (
            <span className="font-medium not-italic text-[var(--foreground)]">
              {item.quoted_author}:{" "}
            </span>
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

      {/* Tags */}
      <div className="mb-3 flex flex-wrap items-center gap-1.5">
        <span className="rounded-full bg-[var(--accent)]/10 px-2.5 py-0.5 text-[11px] font-medium text-[var(--accent)]">
          {contentTypeLabels[item.content_type] || item.content_type}
        </span>
        {item.tags.slice(0, 4).map((tag, i) => (
          <span
            key={i}
            className="rounded-full bg-white/5 px-2.5 py-0.5 text-[11px] text-[var(--muted-foreground)] hover:bg-white/10 transition-colors"
          >
            {tag}
          </span>
        ))}
        {item.journal && (
          <span className="ml-auto text-[10px] text-[var(--muted-foreground)]">
            {item.journal}
          </span>
        )}
      </div>

      {/* Recommendation reason - prominent bar */}
      {item.recommendation_reason && (
        <div className="mt-2 rounded-md bg-[var(--accent)]/5 border-l-2 border-[var(--accent)] px-3 py-2">
          <div className="flex items-start gap-2">
            <span className="mt-0.5 text-[var(--accent)]">🎯</span>
            <p className="text-xs leading-relaxed text-[var(--accent)]">
              {item.recommendation_reason}
            </p>
          </div>
        </div>
      )}

      {/* Report link */}
      {item.meta?.report_path && (
        <a
          href={`/reports/${item.date.substring(0, 4)}/${item.date.substring(5, 7)}/${item.source}/${item.id}`}
          className="mt-3 inline-flex items-center gap-1.5 rounded-md bg-[var(--accent)]/10 px-3 py-1.5 text-xs font-medium text-[var(--accent)] hover:bg-[var(--accent)]/20 transition-colors"
        >
          <FileText className="h-3 w-3" />
          查看解读
        </a>
      )}
    </article>
  );
}
