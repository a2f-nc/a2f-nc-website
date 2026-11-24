# Setting up GitHub and Vercel

One-time setup to put the Stories site on GitHub and have Vercel publish it.
Steps 1 to 4 get the site live. Steps 5 to 8 turn on analytics, finish SEO, and set up the Claude workflow.

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
- Turn on **Require status checks to pass** and add **check** and **test** (the two "Check site" jobs). Add the Vercel check too if you want merges to wait for a successful preview.
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
5. **Before switching:** the blog posts themselves (`/blog/...`) still live on Squarespace, and `blog.html` links to them
   there. Once the domain points at Vercel those links stop working. Either copy the posts into this site first,
   or move them to another home (for example the Acts2 College Substack) and update the links in `blog.html`.

Do this last, after you're happy with the `vercel.app` link, because it switches the live site over.

## 5. Vercel Web Analytics and Speed Insights

The pages already load both scripts (in the `<!-- seo -->` block of each page). To start collecting data:

1. In Vercel: **Project → Analytics → Enable**, and **Project → Speed Insights → Enable**.
2. Data shows up in those tabs a few minutes after people visit. It's privacy-friendly (no cookies, so no cookie banner).
   The scripts only run on the deployed site, not on localhost.

## 6. SEO

Already built into the site:
- A unique `<title>`, meta description and canonical URL on every page.
- Link previews (iMessage, Instagram DMs, GroupMe): Open Graph and Twitter tags with a 1200x630 image from `assets/og/`.
- `sitemap.xml` and `robots.txt` in the repo root.
- Structured data on the home page: the organization (name, logo, Instagram accounts) and the weekly Sunday gathering at UNC.
- The `*.vercel.app` addresses send `noindex`, so Google only lists the real domain.

These all use `https://nc.acts2fellowship.org`. If the final domain is different, change `SITE` in `tools/check.py` and
search-and-replace the domain in the pages, `sitemap.xml` and `robots.txt`.

What's left for you, after step 4 (the domain points at Vercel):
1. Go to search.google.com/search-console, add the domain as a **Domain** property, and verify it with the DNS TXT record it gives you.
2. Under **Sitemaps**, submit `https://nc.acts2fellowship.org/sitemap.xml`.
3. Paste a page link into an iMessage or https://www.opengraph.xyz to check the preview image.

When you add a page: give it a title, description and `<!-- seo -->` block (copy one from another page) and add it to `sitemap.xml`. The check reminds you.

## 7. Request changes by opening an issue (Claude GitHub Action)

The flow: someone opens an issue describing a change → Claude writes it on a branch and opens a pull request →
Vercel comments a preview link → you ask for tweaks by commenting `@claude ...` on the PR → a reviewer approves → merge publishes it.

The workflow file is already in the repo (`.github/workflows/claude.yml`). To turn it on:

1. Make sure the Claude GitHub App is installed on the `a2f-nc` organization with access to this repo:
   https://github.com/apps/claude
2. Add **one** secret under repo **Settings → Secrets and variables → Actions → New repository secret**:
   - `CLAUDE_CODE_OAUTH_TOKEN` if you have a Claude Pro or Max plan: run `claude setup-token` in a terminal and paste the token, or
   - `ANTHROPIC_API_KEY` from console.anthropic.com (pay per use).
3. Optional: create an issue label named `claude`. Adding it to any issue starts Claude on it.
4. Try it: open an issue like "@claude On the UNC page, add the Dec 5 worship night to Events".
   Claude reads `CLAUDE.md` for the site rules, makes the change on a `claude/issue-…` branch, runs `tools/check.py` and the tests,
   and opens a pull request that says "Closes #<issue>". Vercel then comments the preview link on it.
5. To iterate, comment on the PR, for example "@claude make the date bigger and move it above the photo". Claude pushes to the
   same branch and the same preview link updates about a minute later.

Only people with write access to the repo can trigger Claude. Keep step 3's branch protection on so nothing reaches the
live site without an approval.

## 8. Let others see preview links

Vercel protects preview links with a Vercel login by default. If you want other leaders to review previews without a
Vercel account: **Project → Settings → Deployment Protection → Vercel Authentication → Disabled** (or "Only Production Deployments" off).
The live site is always public.
