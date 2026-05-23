# RT Monitor UI Redesign — Design Spec

**Date:** 2026-05-23
**Approach:** Pixel-perfect clone of AIHOT (aihot.virxact.com) adapted for radiotherapy domain
**Scope:** Single-page personal/internal monitoring tool

---

## 1. Goal

Rebuild the RT Monitor frontend to match the visual quality and interaction model of AIHOT, while adapting the content and categories for radiotherapy news/papers monitoring. The result should be a polished, dark-themed content aggregator with rich card metadata.

## 2. Layout & Sidebar

### Sidebar (~180px wide, fixed left)

- **Logo**: "RT Monitor" — "RT" in cyan gradient badge + "Monitor" in plain text
- **Navigation items** (icon + text label):
  - 精选 (Star icon) — active/current page
- **Bottom section**:
  - Theme switcher: three radio buttons (深色 / 跟随系统 / 浅色) with sun/moon/monitor icons
  - No login (personal tool)

### Main Content Area

- Offset by sidebar width (`ml-[180px]`)
- Max-width container (~800px centered)
- Header: Title "精选" + subtitle "放射治疗领域的热点新闻与论文"
- Category filter bar (horizontal tab pills)
- Search bar with "搜索" button
- Date-grouped news feed
- Pagination at bottom

## 3. News Card Design

Each item card follows this structure (top to bottom):

1. **Top row**: Timestamp (HH:MM) + Source name + Source user (optional) + Verified badge + "编辑精选" badge (for editorial picks, gold/amber accent)
2. **Title**: Clickable link to original article, hover turns cyan
3. **Summary**: 2-3 line Chinese summary text
4. **Quoted text** (optional): Blockquote-style section with original author attribution, left border accent
5. **Image gallery** (optional): Thumbnail grid, click to view full-size in lightbox/modal
6. **Bottom row**: Content type badge (color-coded) + topic tags + journal name + AI recommendation score (prominent badge)
7. **Separator**: Thin horizontal line between cards

### Card Styling

- **Dark mode**: `bg-white/[0.03]`, hover `bg-white/[0.06]`, border `border-white/5`
- **Light mode**: white card with subtle shadow
- Rounded corners, padding 16px
- Title hover color: cyan

### Badge Types

- **Editorial badge**: "精选" pill with gold/amber accent
- **Content type badge**: Color-coded (blue=paper, green=news, purple=guideline, orange=research, pink=conference)
- **Recommendation score**: Rounded badge with numeric score
- **Tags**: Small muted pills

## 4. Theme System

### Three-mode switcher

- 深色 (Dark) — default
- 跟随系统 (System) — uses `prefers-color-scheme`
- 浅色 (Light)

### Implementation

- CSS custom properties in `globals.css` (oklch color tokens)
- Tailwind `dark:` variant for component-level theming
- Theme preference saved to `localStorage`
- System mode uses `prefers-color-scheme` media query

### Color Tokens

```
:root (light):
  --background: oklch(1 0 0)           /* white */
  --foreground: oklch(0.15 0 0)        /* near-black */
  --card: oklch(0.98 0 0)             /* off-white */
  --card-foreground: oklch(0.15 0 0)
  --border: oklch(0.9 0 0)
  --muted: oklch(0.95 0 0)
  --muted-foreground: oklch(0.5 0 0)

.dark:
  --background: oklch(0.1 0 0)         /* #0a0a0a */
  --foreground: oklch(1 0 0)
  --card: oklch(0.13 0 0)
  --card-foreground: oklch(1 0 0)
  --border: oklch(0.2 0 0)
  --muted: oklch(0.15 0 0)
  --muted-foreground: oklch(0.5 0 0)
```

## 5. Category Filters

Horizontal pill/tab style matching AIHOT:

- 全部 (All) — default
- 论文 (Papers)
- 行业动态 (Industry News)
- 指南共识 (Guidelines)
- 研究进展 (Research)
- 学术会议 (Conference)

Active state: filled background, inactive: text only with hover. URL parameter `?category=xxx&page=1` for sharing.

## 6. Pagination

- Bottom of feed, standard page numbers
- "上一页" / "下一页" + numbered pages
- Server-side: API accepts `page` and `limit` params
- Response: `{ items: NewsItem[], total: number, page: number, totalPages: number }`
- Default 20 items per page

## 7. Component Architecture

```
src/components/
├── layout/
│   └── Sidebar.tsx              # Fixed sidebar with nav, theme switcher
├── feed/
│   ├── NewsCard.tsx             # Individual news item card
│   ├── DateGroup.tsx            # Date section header + items list
│   ├── FeedList.tsx             # Scrollable feed with date groups
│   ├── CategoryFilter.tsx       # Horizontal tab pills
│   ├── SearchBar.tsx            # Search input + button
│   └── Pagination.tsx           # Page navigation
├── ui/
│   ├── Badge.tsx                # Reusable badge (content type, tags, editorial)
│   ├── ThemeSwitcher.tsx        # Dark/System/Light radio group
│   └── ImageGallery.tsx         # Thumbnail grid + lightbox
└── providers/
    └── ThemeProvider.tsx         # React context for theme state + localStorage
```

## 8. Data Flow

1. `page.tsx` fetches from `/api/items?page=1&limit=20&category=all&search=xxx`
2. API route proxies to Python backend `http://localhost:8001/api/items`
3. Backend returns paginated results from `data/news.json` + `data/papers.json`
4. Response: `{ items: NewsItem[], total: number, page: number, totalPages: number }`

### NewsItem Interface (extended)

```typescript
interface NewsItem {
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
  recommendation_score: number;  // NEW: AI recommendation score
  content_type: string;
  tags: string[];
  category: string;
  pdf_url?: string;
  html_url?: string;
  journal?: string;
  is_featured: boolean;           // NEW: editorial pick flag
  quoted_text?: string;           // NEW: quoted text from author
  quoted_author?: string;         // NEW: quoted text author
  recommendation_reason?: string; // NEW: why this was selected
}
```

## 9. Backend Changes

- Add `page` and `limit` query params to `GET /api/items` in `api_server.py`
- Return pagination metadata in response
- Ensure data collection scripts populate new fields (`is_featured`, `quoted_text`, `recommendation_score`, etc.)

## 10. Implementation Order

1. **Theme system**: CSS variables, ThemeProvider, ThemeSwitcher component
2. **Layout shell**: Sidebar, page.tsx restructuring, responsive container
3. **Components**: Badge, NewsCard, CategoryFilter, SearchBar, Pagination
4. **Feed assembly**: FeedList, DateGroup, wiring to page.tsx
5. **Backend**: Pagination support in api_server.py
6. **Image gallery**: Lightbox/modal for image thumbnails
7. **Polish**: Animations, transitions, responsive adjustments
