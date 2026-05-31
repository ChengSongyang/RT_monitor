export interface NewsItem {
  id: string;
  title: string;
  title_cn?: string;
  content: string;
  summary: string;
  source: string;
  source_type?: string;
  source_user: string;
  source_verified: boolean;
  source_verified_reason: string;
  source_id?: string;
  source_kind?: string;
  source_kind_label?: string;
  source_display_name?: string;
  source_short_name?: string;
  source_homepage?: string;
  source_trust_level?: string;
  source_collection_method?: string;
  source_origin_host?: string;
  source_origin_url?: string;
  source_note?: string;
  mentioned_vendor?: string;
  mentioned_source?: {
    id: string;
    name: string;
    kind: string;
    kind_label: string;
  };
  date: string;
  timestamp: number;
  url: string;
  image_urls: string[];
  hot_score: number;
  recommendation_score: number;
  content_type: string;
  tags: string[];
  category: string;
  pdf_url?: string;
  html_url?: string;
  journal?: string;
  report_path?: string;
  is_featured: boolean;
  quoted_text?: string;
  quoted_author?: string;
  recommendation_reason?: string;
  summary_cn?: string;
  meta?: NewsItemMeta;
  source_info?: SourceInfo;
}

export interface PaginatedResponse {
  items: NewsItem[];
  total: number;
  page: number;
  totalPages: number;
  limit: number;
}

export interface PaperMeta {
  authors?: string;
  journal?: string;
  pdf_url?: string;
  html_url?: string;
  doi?: string;
  report_path?: string;
  report_type?: string;
  citation_count?: number;
  [key: string]: unknown;
}

export interface WechatMeta {
  account_name?: string;
  account_avatar?: string;
  account_id?: string;
  [key: string]: unknown;
}

export interface AIEnrichment {
  score: number;
  is_featured: boolean;
  recommendation_reason: string;
  summary_cn?: string;
}

export interface NewsItemMeta {
  quoted_text?: string;
  quoted_author?: string;
  report_path?: string;
  report_type?: string;
  source_id?: string;
  source_kind?: string;
  source_kind_label?: string;
  origin_host?: string;
  collection_method?: string;
  vendor?: string;
  mentioned_vendor?: string;
  [key: string]: unknown;
}

export type ThemeMode = "dark" | "system" | "light";

export interface Category {
  key: string;
  label: string;
  icon: string;
}

export interface SourceInfo {
  id: string;
  name: string;
  short_name: string;
  kind: string;
  kind_label: string;
  source_type: string;
  homepage: string;
  collection_method: string;
  trust_level: string;
  description: string;
  enabled: boolean;
  origin_host?: string;
  origin_url?: string;
  note?: string;
}

export interface SourceSummary extends SourceInfo {
  count: number;
  featured_count: number;
  latest_date: string;
  latest_timestamp: number;
  categories: Record<string, number>;
  source_types: Record<string, number>;
  origin_hosts: Record<string, number>;
  last_item: {
    id: string;
    title: string;
    url: string;
    date: string;
    category: string;
    source_note?: string;
  } | null;
}

export interface SourceCatalogResponse {
  sources: SourceSummary[];
  total_sources: number;
  active_sources: number;
  total_items: number;
  source_kinds: Record<
    string,
    {
      label: string;
      sources: number;
      active_sources: number;
      items: number;
    }
  >;
  catalog: {
    total_configured: number;
    kind_labels: Record<string, string>;
    configured_kinds: Record<string, number>;
  };
  recent_syncs: Array<{
    source: string;
    items_found: number;
    items_new: number;
    items_updated: number;
    status: string;
    error_message: string;
    created_at: string;
  }>;
}

export interface RssSource {
  id: string;
  name: string;
  short_name: string;
  kind: string;
  kind_label: string;
  source: string;
  source_type: string;
  category: string;
  feed_url: string;
  homepage: string;
  enabled: boolean;
  trust_level: string;
  collection_method: string;
  description: string;
  base_score: number;
  max_items_per_run: number;
  tags: string[];
  last_sync_at: string;
  items_found: number;
  items_new: number;
  items_updated: number;
  status: string;
  error_message: string;
}

export interface RssSourcesResponse {
  sources: RssSource[];
  total_sources: number;
  enabled_sources: number;
  active_sources: number;
}
