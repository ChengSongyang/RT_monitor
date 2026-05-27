"use client";

import { useEffect, useMemo, useState } from "react";
import { Activity, Database, Newspaper, Radio, ShieldCheck } from "lucide-react";
import type { SourceCatalogResponse, SourceSummary } from "@/types";

interface SourceOverviewProps {
  refreshKey?: number;
}

function formatDate(value: string): string {
  if (!value) return "暂无";
  return value.slice(5) || value;
}

function getSourceInitial(source: SourceSummary): string {
  const name = source.short_name || source.name;
  const ascii = name.match(/[A-Za-z0-9]/);
  return (ascii?.[0] || name[0] || "S").toUpperCase();
}

function latestSyncLabel(data: SourceCatalogResponse | null): string {
  const latest = data?.recent_syncs?.[0];
  if (!latest) return "暂无同步";
  const status = latest.status === "success" ? "成功" : "异常";
  return `${latest.source} · ${status}`;
}

export function SourceOverview({ refreshKey = 0 }: SourceOverviewProps) {
  const [data, setData] = useState<SourceCatalogResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function fetchSources() {
      setLoading(true);
      try {
        const res = await fetch("/api/sources");
        const nextData: SourceCatalogResponse = await res.json();
        if (!cancelled) setData(nextData);
      } catch (err) {
        console.error("Failed to fetch source overview:", err);
        if (!cancelled) setData(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchSources();
    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  const activeSources = useMemo(
    () => (data?.sources || []).filter((source) => source.count > 0).slice(0, 8),
    [data]
  );

  const kindRows = useMemo(() => {
    return Object.entries(data?.source_kinds || {})
      .filter(([, value]) => value.sources > 0)
      .sort(([, left], [, right]) => right.items - left.items)
      .slice(0, 5);
  }, [data]);

  return (
    <section className="source-overview-panel">
      <div className="source-overview-head">
        <div>
          <p className="source-kicker">Source Radar</p>
          <h2 className="source-overview-title">信源覆盖</h2>
        </div>
        <span className={`source-sync-pill ${loading ? "source-sync-loading" : ""}`}>
          <Activity className="h-3.5 w-3.5" />
          {loading ? "同步中" : latestSyncLabel(data)}
        </span>
      </div>

      <div className="source-metrics-grid">
        <div className="source-metric">
          <Database className="h-4 w-4" />
          <span>配置</span>
          <strong>{data?.total_sources ?? 0}</strong>
        </div>
        <div className="source-metric">
          <Radio className="h-4 w-4" />
          <span>活跃</span>
          <strong>{data?.active_sources ?? 0}</strong>
        </div>
        <div className="source-metric">
          <Newspaper className="h-4 w-4" />
          <span>内容</span>
          <strong>{data?.total_items ?? 0}</strong>
        </div>
        <div className="source-metric">
          <ShieldCheck className="h-4 w-4" />
          <span>待采集</span>
          <strong>
            {Math.max((data?.total_sources ?? 0) - (data?.active_sources ?? 0), 0)}
          </strong>
        </div>
      </div>

      <div className="source-overview-body">
        <div className="source-kind-list">
          {kindRows.map(([kind, value]) => (
            <div key={kind} className="source-kind-row">
              <span>{value.label}</span>
              <strong>{value.items}</strong>
              <em>{value.active_sources}/{value.sources}</em>
            </div>
          ))}
        </div>

        <div className="source-chip-grid">
          {activeSources.map((source) => (
            <a
              key={source.id}
              className="source-chip"
              href={source.homepage || source.last_item?.url || "#"}
              target="_blank"
              rel="noopener noreferrer"
              title={source.description}
            >
              <span className="source-chip-avatar">{getSourceInitial(source)}</span>
              <span className="source-chip-main">
                <strong>{source.short_name || source.name}</strong>
                <em>{source.kind_label} · {formatDate(source.latest_date)}</em>
              </span>
              <span className="source-chip-count">{source.count}</span>
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}
