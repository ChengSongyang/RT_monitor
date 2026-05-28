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

function getReportHref(item: NewsItem): string {
  const reportPath = item.report_path || item.meta?.report_path;
  const reportParts = reportPath?.split("/") || [];
  if (reportParts.length >= 5 && reportParts[0] === "reports") {
    return `/${reportPath}`;
  }
  const year = item.date?.substring(0, 4) || "2026";
  const month = item.date?.substring(5, 7) || "01";
  return `/reports/${year}/${month}/${encodeURIComponent(item.source)}/${encodeURIComponent(item.id)}`;
}

interface NewsCardProps {
  item: NewsItem;
}

export function NewsCard({ item }: NewsCardProps) {
  const score = Math.round(item.recommendation_score || item.hot_score || 0);
  const displaySource = item.source_display_name || item.source;
  const displayTitle = item.title_cn || item.title;
  const originalTitle = item.title_cn && item.title_cn !== item.title ? item.title : "";
  const primarySummary = item.summary_cn || item.summary;
  const secondarySummary = item.summary_cn && item.summary && item.summary_cn !== item.summary ? item.summary : "";
  const sourceTitle = [
    item.source_collection_method,
    item.source_origin_host,
  ].filter(Boolean).join(" · ") || displaySource;

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
            <span className="source-avatar">{getSourceInitial(displaySource)}</span>
            <span className="timeline-source" title={sourceTitle}>
              {displaySource}
            </span>
            {item.source_kind_label && (
              <span className="timeline-badge timeline-badge-soft">
                {item.source_kind_label}
              </span>
            )}
            {item.source_user && item.source_user !== displaySource && (
              <span className="uc-handle" title={item.source_user}>
                {item.source_user}
              </span>
            )}
            {item.mentioned_vendor && item.mentioned_vendor !== displaySource && (
              <span className="uc-handle" title={item.mentioned_vendor}>
                提及 {item.mentioned_vendor}
              </span>
            )}
            {item.source_verified && item.source_verified_reason !== item.source_kind_label && (
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
          {displayTitle}
          <ExternalLink className="ml-1 inline h-3 w-3 opacity-0 transition-opacity group-hover:opacity-100" />
        </a>

        {originalTitle && (
          <p className="timeline-source-note">{originalTitle}</p>
        )}

        {item.source_note && (
          <p className="timeline-source-note">{item.source_note}</p>
        )}

        {primarySummary && <p className="timeline-summary">{primarySummary}</p>}

        {secondarySummary && (
          <p className="timeline-summary timeline-summary-original">{secondarySummary}</p>
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
            href={getReportHref(item)}
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
