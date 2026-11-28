# Notes for Claude and other agents

This is the static website for Acts2Fellowship NC (UNC and NC State campus ministries).
Contributors are church volunteers, often non-developers, so explain changes in plain language.

## How the site is built
- Plain static HTML in the repo root: `index.html`, `unc.html`, `nc-state.html`, `our-story.html`, `leadership.html`,
  `statement-of-faith.html`, `get-connected.html`, `other-ministries.html`, `blog.html`, `404.html`.
  Blog posts are pages in `blog/` (one folder down, so their links start with `../`), named after their old Squarespace slugs.
  No build step, no dependencies, no npm. Edit the pages directly. (The one script, `tools/new_post.py`, only writes new blog posts; see below.)
- All styles are in `assets/c2.css`; all behavior (story player, reels, swipe deck, Pull up sheet,
  tabs, lightbox, .ics download) is in `assets/c2.js`. Story slides are data in `window.STORIES` at the bottom of each page.
- The header, footer, mobile tab bar and Pull up sheet are repeated in every page. If you change one, change it in all pages.
- `404.html` uses absolute paths (`/assets/...`, `/unc`) because it can be served at any URL. Keep it that way.
- Each page's `<head>` ends with a `<!-- seo -->` block: canonical URL, Open Graph / Twitter tags (1200x630 images in `assets/og/`, `blog-<slug>.jpg` for blog posts),
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

## Tests
- `tests/` holds pytest + Playwright tests (`python3 -m pytest`). Install with `pip install -r requirements-dev.txt`
  and `python3 -m playwright install chromium`. CI runs them on every PR in the "test" job.
- When you add a feature or page, add or extend a test for it. Never delete or weaken a test to make it pass;
  if a test is wrong because the design intentionally changed, update it and say so in the PR.

## Before opening a PR
1. `python3 tools/check.py` says "All good" and `python3 -m pytest` passes.
2. Check the changed pages at desktop and phone width, and open a story, a reel and the Pull up sheet.
3. Say in the PR which pages to check on the Vercel preview.

## Blog posts from issues
New posts are built by a script, not by Claude. Someone opens the "New blog post" issue form
(`.github/ISSUE_TEMPLATE/blog-post.yml`: Post title, Author, Post as Markdown, Post image), and `.github/workflows/new-blog-post.yml`
runs `python3 tools/new_post.py --issue-body ...`, which writes `blog/<slug>.html` (copied from the newest post), the three photo sizes,
the first card on `blog.html`, the `sitemap.xml` entry, and the Older/Newer post links on the new post and the previous newest one.
The workflow then opens a pull request on branch `claude/issue-<N>-blog-<slug>`. `claude.yml` leaves these issues alone when they are opened.
- When someone replies on the issue, you update that same pull request. Edit the post's HTML directly (text, photo alt text, summary, title).
  If you change a title or slug, also update `blog.html`, `sitemap.xml`, the `post-nav` links on the neighbor posts and the `assets/og/blog-<slug>.jpg` name.
- Check the photo `alt` text the script chose (it falls back to "Photo for “<title>”") and improve it if you can see what the photo shows.
- Don't hand-build new posts. If the script can't do something, fix `tools/new_post.py` and add a test to `tests/test_new_post.py`.
- Photos dragged into the post text are saved to `assets/blog/posts/`; never leave links to `github.com/user-attachments`.
