# Notes for Claude and other agents

This is the static website for Acts2Fellowship NC (UNC and NC State campus ministries).
Contributors are church volunteers, often non-developers, so explain changes in plain language.

## How the site is built
- Plain static HTML in the repo root: `index.html`, `unc.html`, `nc-state.html`, `our-story.html`, `leadership.html`,
  `statement-of-faith.html`, `get-connected.html`, `other-ministries.html`, `blog.html`, `404.html`.
  Blog posts are pages in `blog/` (one folder down, so their links start with `../`), named after their old Squarespace slugs.
  No build step, no dependencies, no npm. Edit the pages directly.
- All styles are in `assets/c2.css`; all behavior (story player, reels, swipe deck, Pull up sheet,
  tabs, lightbox, .ics download) is in `assets/c2.js`. Story slides are data in `window.STORIES` at the bottom of each page.
- The header, footer, mobile tab bar and Pull up sheet are repeated in every page. If you change one, change it in all pages.
- `404.html` uses absolute paths (`/assets/...`, `/unc`) because it can be served at any URL. Keep it that way.
- Each page's `<head>` ends with a `<!-- seo -->` block: canonical URL, Open Graph / Twitter tags (images in `assets/og/`),
  Vercel Analytics and Speed Insights scripts, and on the home page JSON-LD structured data. New pages need one, plus an
  entry in `sitemap.xml`. The live domain is `https://nc.acts2fellowship.org` (`SITE` in `tools/check.py`).
- Preview: `python3 -m http.server 8000` and open http://localhost:8000.
- Check: `python3 tools/check.py` (links, alt text, titles and descriptions, banned copy, asset sizes, unused assets). CI runs it on every PR.
- Hosting: Vercel serves the repo root as static files. `vercel.json` turns on clean URLs (`/unc`), redirects the
  old Squarespace paths, and caches assets for a week. Pull requests get preview deployments, and `main` is production.

## Design rules
- Look: Concept 2 "Stories". Fonts are Dela Gothic One (titles, Google Fonts) and Glacial Indifference (everything else,
  self-hosted). Brand colors are CSS variables in `c2.css`: `--green`, `--brown`, `--yellow`, `--blue` (UNC), `--maroon` (NC State).
  UNC pages use `body.unc`, NC State pages use `body.ncsu`, which set `--accent`.
- UNC and NC State are peers. Neither is a subpage of the other.
- The site must work at phone width (390px) with no sideways scrolling, by keyboard, and with "reduce motion" on
  (stories don't auto-advance, reels don't autoplay, no reveal animations). Keep new animations behind `.motion` / the reduced-motion media query.
- Copy: the message is that students seek, learn and grow in Jesus. Don't use the phrase "come as you are".
  Keep all existing content unless asked. Don't invent facts, dates, names or quotes.
- Photos: real community photos, bright and sharp with faces visible, and a mix of people. No photo or clip appears twice
  across the site. Every `<img>` needs an `alt` that describes it. Only commit files the site actually uses.

## Before opening a PR
1. `python3 tools/check.py` says "All good".
2. Check the changed pages at desktop and phone width, and open a story, a reel and the Pull up sheet.
3. Say in the PR which pages to check on the Vercel preview.
