# AIHOT Gap Analysis

Target: https://aihot.virxact.com/
Date: 2026-05-27

## Key Findings

- The target feed is a timeline, not a plain card list. Desktop uses an 86px time column, 28px rail, and a wide card column; mobile keeps the rail with a 44px time column and 16px rail.
- The header controls live inside one translucent hero panel with title, subtitle, segmented tabs, and compact search. The previous local version had separate heading, tabs, and search rows with less visual hierarchy.
- The target desktop content fills the available area after the 180px sidebar, with about 28px main padding and a 1038px content region at a 1280px viewport. The previous local version capped the feed at 800px.
- Cards use a dense metadata header, score badge, selected badge, compact tags, a divider, and a green recommendation bar. The previous local cards had heavier generic borders, emoji-led recommendation blocks, and no timeline anchor.
- Mobile uses a sticky brand bar, hidden drawer sidebar, full-width header panel, and clipped-safe timeline columns. The previous local mobile layout had a floating hamburger and no centered brand bar.

## Implemented Changes

- Reworked global design tokens to match AIHOT's dark surface system, borders, shadows, cyan/emerald/amber accents, and responsive app shell.
- Rebuilt the sidebar with a large brand tile, AIHOT-like nav density, active cyan gradient item, mobile drawer, and sticky mobile brand bar.
- Converted the page header into a single glass panel with compact segmented filters and search.
- Converted date groups and news cards into the target-style timeline layout on desktop and mobile.
- Reworked cards with source avatar, source metadata, featured/score badges, compact tags, divider, and recommendation bar.
- Fixed mobile overflow where inner controls were widening the panel and card column beyond the viewport.
