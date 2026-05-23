# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered website reverse-engineering template that clones any website into a clean Next.js codebase. The `/clone-website` skill extracts design tokens, assets, and component specs, then dispatches parallel builder agents in git worktrees to reconstruct each section.

## Tech Stack

- **Framework:** Next.js 16 (App Router, React 19, TypeScript strict)
- **UI:** shadcn/ui (Radix primitives, Tailwind CSS v4, `cn()` utility)
- **Icons:** Lucide React (replaced by extracted SVGs during cloning)
- **Styling:** Tailwind CSS v4 with oklch design tokens
- **Deployment:** Vercel (standalone output mode)

## Commands

```bash
npm run dev        # Start dev server
npm run build      # Production build
npm run start      # Start production server
npm run lint       # ESLint check
npm run typecheck  # TypeScript check (tsc --noEmit)
npm run check      # Run lint + typecheck + build
```

Docker:
```bash
docker compose up app --build  # Build and run production
docker compose up dev --build  # Dev mode on port 3001
```

## Architecture

- `src/app/` — Next.js App Router pages and API routes
- `src/app/api/items/route.ts` — GET endpoint for news items
- `src/app/api/refresh/route.ts` — POST endpoint to refresh data
- `src/components/ui/` — shadcn/ui primitives (Button uses @base-ui/react)
- `src/lib/utils.ts` — `cn()` utility for className merging
- `public/` — Static assets (images, videos, SEO files)
- `docs/research/` — Component specs and design token extraction output
- `scripts/` — Sync scripts for agent rules and skills

## Code Style

- TypeScript strict mode, no `any`
- Named exports, PascalCase components, camelCase utils
- Tailwind utility classes, no inline styles
- 2-space indentation
- Mobile-first responsive design

## Key Patterns

- Path aliases: `@/*` maps to `./src/*`
- CSS variables for theming in `globals.css` (`:root` and `.dark` blocks)
- Component variants via `class-variance-authority` (CVA)
- Client components use `"use client"` directive
- Chinese locale (zh-CN) for UI text

## Agent Workflow

- Each builder agent works in its own git worktree branch
- Merge work at end, resolving conflicts with full orchestrator context
- After editing `AGENTS.md`: run `bash scripts/sync-agent-rules.sh`
- After editing `.claude/skills/clone-website/SKILL.md`: run `node scripts/sync-skills.mjs`

## Clone Pipeline Phases

1. **Reconnaissance** — Screenshots, design token extraction, interaction sweep
2. **Foundation** — Update fonts, colors, globals, download assets
3. **Component Spec** — Write spec files to `docs/research/components/`
4. **Parallel Build** — Dispatch builders in worktrees (one per section)
5. **Assembly & QA** — Merge worktrees, wire page, visual diff against original

## Important Constraints

- Builder prompts must stay under ~150 lines; split complex sections
- Every CSS value must come from `getComputedStyle()`, not estimation
- Identify interaction model (click/scroll/hover/time) BEFORE building
- Extract ALL states (not just default) for stateful components
- Spec files in `docs/research/components/` are mandatory before dispatching builders
- Verify `npx tsc --noEmit` passes after each builder completes
