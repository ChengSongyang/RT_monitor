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
  className?: string;
}

export function Sidebar({ className }: SidebarProps) {
  const [open, setOpen] = useState(false);

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
            className="side-link side-link-active"
          >
            <Sparkles className="side-icon" />
            <span>精选</span>
          </Link>
          <a
            href="#feed"
            onClick={() => setOpen(false)}
            className="side-link"
          >
            <ListFilter className="side-icon" />
            <span>全部动态</span>
          </a>
          <a
            href="#top"
            onClick={() => setOpen(false)}
            className="side-link"
          >
            <FileClock className="side-icon" />
            <span>筛选搜索</span>
          </a>
          <a
            href="#feed"
            onClick={() => setOpen(false)}
            className="side-link"
          >
            <BookOpenText className="side-icon" />
            <span>研究日报</span>
          </a>
          <button
            type="button"
            className="side-link text-left"
            disabled
            title="后续可接入信源管理"
          >
            <Rss className="side-icon" />
            <span>信源提报</span>
          </button>
          <a
            href="https://aihot.virxact.com/"
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
