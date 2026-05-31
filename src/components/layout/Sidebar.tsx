"use client";

import { useState } from "react";
import Link from "next/link";
import {
  BookOpenText,
  ExternalLink,
  FileClock,
  ListFilter,
  Menu,
  Rss,
  Sparkles,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ThemeSwitcher } from "@/components/ui/ThemeSwitcher";

interface SidebarProps {
  active?: "home" | "rss-sources";
  className?: string;
}

export function Sidebar({ active = "home", className }: SidebarProps) {
  const [open, setOpen] = useState(false);
  const feedHref = active === "home" ? "#feed" : "/#feed";
  const topHref = active === "home" ? "#top" : "/#top";

  return (
    <>
      <div className="app-mobile-bar">
        <button
          onClick={() => setOpen(true)}
          className="app-hamburger"
          aria-label="打开菜单"
        >
          <Menu className="h-5 w-5" />
        </button>
        <Link href="/" className="app-mobile-brand">
          <span className="app-mobile-brand-text">RT MONITOR</span>
        </Link>
        <div className="app-mobile-bar-spacer" />
      </div>

      {open && (
        <div
          className="sidebar-backdrop md:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      <aside
        className={cn(
          "sidebar-panel",
          open && "sidebar-panel-open",
          className
        )}
      >
        <button
          onClick={() => setOpen(false)}
          className="sidebar-close"
          aria-label="关闭菜单"
        >
          <X className="h-5 w-5" />
        </button>

        <Link href="/" className="sidebar-brand" onClick={() => setOpen(false)}>
          <span className="brand-logo" aria-label="RT Monitor">
            <span>RT</span>
            <span className="brand-logo-orbit" aria-hidden="true" />
            <span className="brand-logo-accent">MONITOR</span>
          </span>
        </Link>

        <nav className="side-nav">
          <Link
            href="/"
            onClick={() => setOpen(false)}
            className={cn("side-link", active === "home" && "side-link-active")}
          >
            <Sparkles className="side-icon" />
            <span>精选</span>
          </Link>
          <a
            href={feedHref}
            onClick={() => setOpen(false)}
            className="side-link"
          >
            <ListFilter className="side-icon" />
            <span>全部动态</span>
          </a>
          <a
            href={topHref}
            onClick={() => setOpen(false)}
            className="side-link"
          >
            <FileClock className="side-icon" />
            <span>筛选搜索</span>
          </a>
          <a
            href={feedHref}
            onClick={() => setOpen(false)}
            className="side-link"
          >
            <BookOpenText className="side-icon" />
            <span>研究日报</span>
          </a>
          <Link
            href="/rss-sources"
            onClick={() => setOpen(false)}
            className={cn(
              "side-link",
              active === "rss-sources" && "side-link-active"
            )}
          >
            <Rss className="side-icon" />
            <span>RSS 订阅源</span>
          </Link>
          <a
            href="http://47.77.216.151:24830/"
            target="_blank"
            rel="noopener noreferrer"
            className="side-link"
          >
            <ExternalLink className="side-icon" />
            <span>AI 热点</span>
          </a>
        </nav>

        <div className="sidebar-footer">
          <ThemeSwitcher />
        </div>
      </aside>
    </>
  );
}
