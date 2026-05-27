import { ImageGallery } from "@/components/ui/ImageGallery";
import { ExternalLink, FileText, Sparkles } from "lucide-react";
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

function getSourceInitial(source: string): string {
  const trimmed = source.trim();
  if (!trimmed) return "R";
  const ascii = trimmed.match(/[A-Za-z0-9]/);
  return (ascii?.[0] || trimmed[0]).toUpperCase();
}

function getScoreClass(score: number): string {
  if (score >= 70) return "score-high";
  if (score >= 45) return "score-mid";
  return "score-muted";
}

interface NewsCardProps {
  item: NewsItem;
}

export function NewsCard({ item }: NewsCardProps) {
  const score = Math.round(item.recommendation_score || item.hot_score || 0);

  return (
    <div
      className={`timeline-item ${item.is_featured ? "timeline-item-starred" : ""}`}
    >
      <div className="timeline-time">{formatTime(item.timestamp)}</div>
      <div className="timeline-rail" aria-hidden="true">
        <span className="timeline-dot" />
      </div>

      <article className="timeline-card group">
        <div className="timeline-card-head">
          <div className="timeline-head-left">
            <span className="source-avatar">{getSourceInitial(item.source)}</span>
            <span className="timeline-source" title={item.source}>
              {item.source}
            </span>
            {item.source_user && item.source_user !== item.source && (
              <span className="uc-handle" title={item.source_user}>
                {item.source_user}
              </span>
            )}
            {item.source_verified && (
              <span className="timeline-badge">
                {item.source_verified_reason || "已认证"}
              </span>
            )}
          </div>
          <div className="timeline-head-right">
            {item.is_featured && (
              <span className="timeline-selected-badge">精选</span>
            )}
            {score > 0 && (
              <span className={`timeline-score ${getScoreClass(score)}`}>
                {score}
              </span>
            )}
          </div>
        </div>

        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="timeline-title"
        >
          {item.title}
          <ExternalLink className="ml-1 inline h-3 w-3 opacity-0 transition-opacity group-hover:opacity-100" />
        </a>

        {item.summary && <p className="timeline-summary">{item.summary}</p>}

        {item.summary_cn && item.summary_cn !== item.summary && (
          <p className="timeline-summary">{item.summary_cn}</p>
        )}

        {item.quoted_text && (
          <blockquote className="timeline-quote">
            {item.quoted_author && (
              <span className="font-semibold not-italic text-[var(--text-1)]">
                {item.quoted_author}:{" "}
              </span>
            )}
            {item.quoted_text}
          </blockquote>
        )}

        {item.image_urls && item.image_urls.length > 0 && (
          <ImageGallery images={item.image_urls} />
        )}

        <div className="timeline-tags">
          <span className="tag tag-primary">
            {contentTypeLabels[item.content_type] || item.content_type}
          </span>
          {item.tags.slice(0, 4).map((tag, i) => (
            <span key={`${tag}-${i}`} className="tag" title={tag}>
              {tag}
            </span>
          ))}
          {item.journal && (
            <span className="tag" title={item.journal}>
              {item.journal}
            </span>
          )}
        </div>

        {(item.recommendation_reason || item.meta?.report_path) && (
          <div className="timeline-divider" />
        )}

        {item.recommendation_reason && (
          <div className="recommendation-bar">
            <Sparkles className="recommendation-icon" />
            <p>推荐理由：{item.recommendation_reason}</p>
          </div>
        )}

        {item.meta?.report_path && (
          <a
            href={`/reports/${item.date.substring(0, 4)}/${item.date.substring(5, 7)}/${item.source}/${item.id}`}
            className="mt-3 inline-flex items-center gap-1.5 rounded-md border border-[var(--border-strong)] bg-[var(--surface-1)] px-3 py-1.5 text-xs font-medium text-[var(--accent-cyan)] transition-colors hover:bg-[var(--surface-2)]"
          >
            <FileText className="h-3 w-3" />
            查看解读
          </a>
        )}
      </article>
    </div>
  );
}
