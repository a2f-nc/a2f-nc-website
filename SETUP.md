# Setting up GitHub and Vercel

One-time setup to put the Stories site on GitHub and have Vercel publish it.
Steps 1 to 4 get the site live. Steps 5 to 7 are optional upgrades you can add any time.

## 1. Put the site on GitHub

The site's repo is **https://github.com/a2f-nc/a2f-nc-website** (it starts out empty).

1. In a terminal, from this folder:
   ```sh
   git init -b main
   git add .
   git commit -m "Stories design"
   git remote add origin https://github.com/a2f-nc/a2f-nc-website.git
   git push -u origin main
   ```
2. Open the repo's **Actions** tab. The "Check site" workflow should run and pass.

## 2. Connect Vercel

1. Sign in at vercel.com with GitHub, then **Add New → Project** and import `a2f-nc/a2f-nc-website`.
   If it isn't listed, click **Adjust GitHub App Permissions** and give Vercel access to the `a2f-nc` organization.
2. Framework preset: **Other**. Leave Build Command, Output Directory and Install Command empty
   (there's no build step; Vercel serves the repo root as-is).
3. Click **Deploy**. You'll get a `*.vercel.app` link for the live site.

From now on:
- Each pull request gets a preview deployment, and the Vercel bot comments the link on the PR.
- Merging into `main` updates the live site.

## 3. Protect `main` (so changes go through a pull request)

GitHub → repo **Settings → Rules → Rulesets → New branch ruleset** (or **Settings → Branches → Add rule**):
- Target: the default branch (`main`).
- Turn on **Require a pull request before merging**, with **Required approvals: 1**.
- Turn on **Require status checks to pass** and add **check** (the "Check site" job). Add the Vercel check too if you want merges to wait for a successful preview.
- Turn on **Block force pushes**.

Note: GitHub doesn't let you approve your own pull request. If you're the only person with write access,
either add a second reviewer (another leader) as a collaborator, or add yourself to the ruleset's bypass list
so you can still merge your own PRs.

## 4. Point the real domain at Vercel

1. In Vercel: **Project → Settings → Domains → Add**, and enter the domain (for example `nc.acts2fellowship.org`).
2. Vercel shows the DNS record to add (for a subdomain, usually a `CNAME` to `cname.vercel-dns.com`).
   Add it wherever the domain's DNS is managed (today that may be Squarespace or whoever runs `acts2fellowship.org`).
3. Once the record is live, Vercel issues the HTTPS certificate on its own.
4. Old Squarespace links keep working: `vercel.json` redirects `/unc-acts2fellowship`, `/a2f-nc-state`, `/about-us`,
   `/about-our-story`, `/ministries` and `/resources` to the matching new page.
5. Old blog post links keep working too: each post is a page in `blog/` named after its old Squarespace address,
   so `/blog/how-tacos-changed-my-college-life` opens `blog/how-tacos-changed-my-college-life.html`.
   If a new post goes up on Squarespace before the switch, copy it into `blog/` as well (see README).

Do this last, after you're happy with the `vercel.app` link, because it switches the live site over.

## 5. Optional: Vercel Web Analytics and Speed Insights

Privacy-friendly visitor counts (no cookie banner needed) and real-world page speed.

1. In Vercel: **Project → Analytics → Enable**, and **Project → Speed Insights → Enable**.
2. Add these two lines just before `</head>` in every page (`index.html`, `unc.html`, `nc-state.html`,
   `statement-of-faith.html`, `404.html`):
   ```html
   <script defer src="/_vercel/insights/script.js"></script>
   <script defer src="/_vercel/speed-insights/script.js"></script>
   ```
3. Merge, and data starts showing in Vercel within a few minutes of visits. (They only load on the deployed site, not on localhost.)

## 6. Optional: SEO basics

What to add so the site shows up well in Google and in link previews (iMessage, Instagram DMs, GroupMe):

- **Titles and descriptions**: every page already has a unique `<title>` and meta description (the check enforces it).
- **Canonical URL** on each page, for example `<link rel="canonical" href="https://nc.acts2fellowship.org/unc">`.
- **Open Graph / link preview tags** on each page: `og:title`, `og:description`, `og:url`, `og:type`, and an
  `og:image` (a 1200x630 JPG per page, for example a group photo with the A2F wordmark), plus `twitter:card` set to `summary_large_image`.
- **`sitemap.xml`** in the repo root listing `/`, `/unc`, `/nc-state`, `/statement-of-faith`.
- **`robots.txt`** in the repo root: allow everything and point to the sitemap.
- **Structured data**: a JSON-LD `Organization` block on the home page (name, logo, Instagram links) and an
  `Event` block for the weekly Sunday gathering (211 W Cameron Ave, Chapel Hill, 11:30 am).
- **Google Search Console**: add the domain at search.google.com/search-console, verify it with the DNS TXT
  record it gives you, then submit `https://YOUR-DOMAIN/sitemap.xml`. Do this after step 4.

These need the final domain name, so add them once you know it.

## 7. Optional: request changes by opening an issue (Claude GitHub Action)

The flow: someone opens an issue describing a change → Claude writes it on a branch and opens a pull request →
Vercel comments a preview link → you ask for tweaks by commenting `@claude ...` on the PR → a reviewer approves → merge publishes it.

1. Install the Claude GitHub App on the repo: https://github.com/apps/claude (choose the `a2f-nc` organization and the `a2f-nc-website` repo)
   (or, from Claude Code in this folder, run `/install-github-app`, which does steps 1 to 3 for you).
2. Add a secret under **Settings → Secrets and variables → Actions**: either `ANTHROPIC_API_KEY`
   (from console.anthropic.com) or `CLAUDE_CODE_OAUTH_TOKEN` (run `claude setup-token` if you have a Claude Pro or Max plan).
3. Add `.github/workflows/claude.yml`:
   ```yaml
   name: Claude
   on:
     issues:
       types: [opened, assigned, labeled]
     issue_comment:
       types: [created]
     pull_request_review_comment:
       types: [created]
     pull_request_review:
       types: [submitted]
   permissions:
     contents: write
     pull-requests: write
     issues: write
     id-token: write
     actions: read
   jobs:
     claude:
       if: |
         (github.event_name == 'issues' && (contains(github.event.issue.body, '@claude') || github.event.label.name == 'claude')) ||
         (github.event_name != 'issues' && contains(toJSON(github.event), '@claude'))
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
           with:
             fetch-depth: 1
         - uses: anthropics/claude-code-action@v1
           with:
             claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
             # or: anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
   ```
4. Use it: open an issue like "@claude On the UNC page, add the Dec 5 worship night to Events", or add the
   `claude` label to an issue. Claude reads `CLAUDE.md` for the site rules, runs `tools/check.py`, and
   replies with a link to the branch or pull request.
5. Keep step 3's branch protection on so nothing reaches the live site without an approval.
   Only people with write access to the repo can trigger Claude.
