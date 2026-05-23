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

      {/* Report link */}
      {item.meta?.report_path && (
        <a
          href={`/reports/${item.date.substring(0, 4)}/${item.date.substring(5, 7)}/${item.source}/${item.id}`}
          className="mt-2 inline-flex items-center gap-1 text-xs text-[var(--accent)] hover:underline"
        >
          查看解读 →
        </a>
      )}
    </article>
  );
}
