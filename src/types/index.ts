export interface NewsItem {
  id: string;
  title: string;
  content: string;
  summary: string;
  source: string;
  source_user: string;
  source_verified: boolean;
  source_verified_reason: string;
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
  is_featured: boolean;
  quoted_text?: string;
  quoted_author?: string;
  recommendation_reason?: string;
  summary_cn?: string;
  meta?: NewsItemMeta;
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
  [key: string]: unknown;
}

export type ThemeMode = "dark" | "system" | "light";

export interface Category {
  key: string;
  label: string;
  icon: string;
}
