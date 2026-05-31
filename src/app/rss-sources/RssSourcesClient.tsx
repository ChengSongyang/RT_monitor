"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertCircle, CheckCircle2, ExternalLink, Radio, Rss } from "lucide-react";
import { Sidebar } from "@/components/layout/Sidebar";
import type { RssSource, RssSourcesResponse } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8001";
const RSS_ENDPOINTS = [
  "/api/rss-sources",
  "/api/sources?view=rss",
  `${API_BASE_URL}/api/sources?view=rss`,
  `${API_BASE_URL}/api/rss-sources`,
];

function isRssSourcesResponse(value: unknown): value is RssSourcesResponse {
  if (!value || typeof value !== "object") return false;

  const candidate = value as Partial<RssSourcesResponse>;
  return (
    Array.isArray(candidate.sources) &&
    typeof candidate.total_sources === "number" &&
    typeof candidate.enabled_sources === "number" &&
    typeof candidate.active_sources === "number"
  );
}

async function fetchJson(url: string): Promise<unknown> {
  const response = await fetch(url, { cache: "no-store" });
  const data: unknown = await response.json();

  if (!response.ok) {
    throw new Error("RSS 订阅源状态加载失败");
  }

  return data;
}

async function fetchRssSources(): Promise<RssSourcesResponse> {
  for (const endpoint of RSS_ENDPOINTS) {
    try {
      const data = await fetchJson(endpoint);
      if (isRssSourcesResponse(data)) return data;
    } catch (error) {
      console.warn(`RSS source fetch failed for ${endpoint}:`, error);
    }
  }

  throw new Error("RSS 订阅源状态加载失败");
}

function formatSyncTime(value: string): string {
  if (!value) return "暂无同步";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function statusLabel(source: RssSource): string {
  if (!source.enabled) return "已停用";
  if (source.error_message) return "同步异常";
  if (source.status === "success") return "同步正常";
  return source.status || "等待同步";
}

function SourceCard({ source }: { source: RssSource }) {
  const hasError = Boolean(source.error_message);

  return (
    <article className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface-card)] p-5 shadow-[var(--shadow-card)] transition hover:border-[var(--border-emphasis)] hover:shadow-[var(--shadow-card-hover)]">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-[var(--border)] bg-[var(--surface-raised)] px-2.5 py-1 text-xs text-[var(--muted-foreground)]">
              {source.kind_label || source.kind}
            </span>
            <span className="rounded-full border border-[var(--border)] px-2.5 py-1 text-xs text-[var(--muted-foreground)]">
              {source.source_type || "RSS/Atom"}
            </span>
          </div>
          <h2 className="text-lg font-semibold text-[var(--foreground)]">
            {source.short_name || source.name}
          </h2>
          <p className="text-sm leading-6 text-[var(--muted-foreground)]">
            {source.description || source.name}
          </p>
        </div>

        <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${
          source.enabled
            ? "bg-emerald-500/10 text-emerald-400"
            : "bg-slate-500/10 text-[var(--muted-foreground)]"
        }`}>
          {source.enabled ? (
            <CheckCircle2 className="h-3.5 w-3.5" />
          ) : (
            <AlertCircle className="h-3.5 w-3.5" />
          )}
          {statusLabel(source)}
        </span>
      </div>

      <div className="mt-5 grid gap-3 text-sm sm:grid-cols-3">
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-raised)] p-3">
          <p className="text-xs text-[var(--muted-foreground)]">最近同步</p>
          <strong className="mt-1 block text-[var(--foreground)]">
            {formatSyncTime(source.last_sync_at)}
          </strong>
        </div>
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-raised)] p-3">
          <p className="text-xs text-[var(--muted-foreground)]">发现</p>
          <strong className="mt-1 block text-[var(--foreground)]">
            {source.items_found}
          </strong>
        </div>
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-raised)] p-3">
          <p className="text-xs text-[var(--muted-foreground)]">新增 / 更新</p>
          <strong className="mt-1 block text-[var(--foreground)]">
            {source.items_new} / {source.items_updated}
          </strong>
        </div>
      </div>

      <div className="mt-5 space-y-3 border-t border-[var(--border)] pt-4 text-sm">
        <div className="flex min-w-0 items-start gap-2 text-[var(--muted-foreground)]">
          <Rss className="mt-0.5 h-4 w-4 shrink-0" />
          <a
            href={source.feed_url}
            target="_blank"
            rel="noopener noreferrer"
            className="break-all text-[var(--foreground)] hover:text-[var(--primary)]"
          >
            {source.feed_url}
          </a>
        </div>
        {source.homepage && (
          <a
            href={source.homepage}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-[var(--muted-foreground)] hover:text-[var(--primary)]"
          >
            来源主页
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        )}
        {hasError && (
          <p className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-red-300">
            {source.error_message}
          </p>
        )}
      </div>
    </article>
  );
}

export default function RssSourcesClient() {
  const [data, setData] = useState<RssSourcesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function fetchSources() {
      setLoading(true);
      setError("");

      try {
        const nextData = await fetchRssSources();
        if (!cancelled) setData(nextData);
      } catch (err) {
        console.error("Failed to fetch RSS sources:", err);
        if (!cancelled) {
          setData(null);
          setError(err instanceof Error ? err.message : "RSS 订阅源状态加载失败");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchSources();
    return () => {
      cancelled = true;
    };
  }, []);

  const sources = useMemo(() => data?.sources || [], [data]);

  return (
    <div className="app-shell text-[var(--foreground)]">
      <Sidebar active="rss-sources" />

      <main className="app-main">
        <div id="top" className="app-main-inner">
          <section className="page-header-feed mb-4">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="source-kicker">Source Radar</p>
                <h1 className="page-title">RSS 订阅源</h1>
                <p className="page-subtitle">
                  查看当前 RSS/Atom 信源配置、同步状态与采集结果
                </p>
              </div>
              <span className="source-sync-pill">
                <Radio className="h-3.5 w-3.5" />
                {loading ? "加载中" : `${data?.enabled_sources ?? 0}/${data?.total_sources ?? 0} 启用`}
              </span>
            </div>
          </section>

          <div className="mb-4 grid gap-3 sm:grid-cols-3">
            <div className="source-metric">
              <Rss className="h-4 w-4" />
              <span>订阅源</span>
              <strong>{data?.total_sources ?? 0}</strong>
            </div>
            <div className="source-metric">
              <CheckCircle2 className="h-4 w-4" />
              <span>已启用</span>
              <strong>{data?.enabled_sources ?? 0}</strong>
            </div>
            <div className="source-metric">
              <Radio className="h-4 w-4" />
              <span>有同步记录</span>
              <strong>{data?.active_sources ?? 0}</strong>
            </div>
          </div>

          {error && (
            <div className="mb-4 rounded-[var(--radius)] border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
              {error}
            </div>
          )}

          {loading ? (
            <div className="flex h-64 items-center justify-center rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface-card)] text-[var(--muted-foreground)]">
              正在加载 RSS 订阅源...
            </div>
          ) : sources.length > 0 ? (
            <div className="grid gap-4">
              {sources.map((source) => (
                <SourceCard key={source.id} source={source} />
              ))}
            </div>
          ) : (
            <div className="rounded-[var(--radius)] border border-dashed border-[var(--border-emphasis)] bg-[var(--surface-card)] py-16 text-center text-[var(--muted-foreground)]">
              暂无 RSS 订阅源
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
