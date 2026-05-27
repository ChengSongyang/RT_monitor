"use client";

import { useState, useEffect, useCallback } from "react";
import { RefreshCw } from "lucide-react";
import { Sidebar } from "@/components/layout/Sidebar";
import { CategoryFilter } from "@/components/feed/CategoryFilter";
import { SearchBar } from "@/components/feed/SearchBar";
import { FeedList } from "@/components/feed/FeedList";
import { Pagination } from "@/components/feed/Pagination";
import { SourceOverview } from "@/components/feed/SourceOverview";
import type { NewsItem, PaginatedResponse } from "@/types";

const ITEMS_PER_PAGE = 20;

export default function HomePage() {
  const [items, setItems] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [sourceRefreshKey, setSourceRefreshKey] = useState(0);

  const fetchItems = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (activeCategory !== "all") params.append("category", activeCategory);
      if (searchQuery) params.append("search", searchQuery);
      params.append("page", String(page));
      params.append("limit", String(ITEMS_PER_PAGE));

      const res = await fetch(`/api/items?${params.toString()}`);
      const data: PaginatedResponse = await res.json();
      setItems(data.items || []);
      setTotalPages(data.totalPages || 1);
      setTotal(data.total || 0);
    } catch (err) {
      console.error("Failed to fetch items:", err);
    } finally {
      setLoading(false);
    }
  }, [activeCategory, searchQuery, page]);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await fetch("/api/refresh", { method: "POST" });
      await fetchItems();
      setSourceRefreshKey((value) => value + 1);
    } catch (err) {
      console.error("Failed to refresh:", err);
    } finally {
      setRefreshing(false);
    }
  };

  const handleCategoryChange = (cat: string) => {
    setActiveCategory(cat);
    setPage(1);
  };

  const handleSearch = () => {
    setSearchQuery(searchInput);
    setPage(1);
  };

  return (
    <div className="app-shell text-[var(--foreground)]">
      <Sidebar />

      <main className="app-main">
        <div id="top" className="app-main-inner">
          <section className="page-header-feed mb-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="page-title">精选</h1>
                <p className="page-subtitle">
                  放射治疗领域的热点新闻与论文
                </p>
              </div>
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="refresh-btn"
              >
                <RefreshCw
                  className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`}
                />
                <span className="refresh-label">刷新数据</span>
              </button>
            </div>

            <div className="page-divider" />

            <div className="feed-toolbar-row">
              <CategoryFilter
                activeCategory={activeCategory}
                onChange={handleCategoryChange}
              />
              <SearchBar
                value={searchInput}
                onChange={setSearchInput}
                onSearch={handleSearch}
              />
            </div>
          </section>

          <SourceOverview refreshKey={sourceRefreshKey} />

          <FeedList items={items} loading={loading} />

          <Pagination
            page={page}
            totalPages={totalPages}
            onPageChange={setPage}
          />

          {total > 0 && (
            <p className="py-4 text-center text-xs text-[var(--muted-foreground)]">
              共 {total} 条
            </p>
          )}
        </div>
      </main>
    </div>
  );
}
