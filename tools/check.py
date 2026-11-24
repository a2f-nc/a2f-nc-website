#!/usr/bin/env python3
"""Site check for Acts2Fellowship NC. Run from the repo root: python3 tools/check.py

Fails (exit 1) if:
  - a page links to a local file that doesn't exist
  - an <img> has no alt attribute
  - a page has no <title> or meta description
  - banned copy shows up (see BANNED)
  - a file in assets/ is over the size limit
  - a file in assets/ isn't used by any page, stylesheet or script
Python 3 standard library only.
"""
import os, re, sys
from urllib.parse import urlparse, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://nc.acts2fellowship.org"  # the live address (used in canonical, og:image, sitemap)
BANNED = ["come as you are"]          # copy we agreed not to use
MAX_MB = 5                            # per file in assets/
IGNORE = {".DS_Store"}

errors = []
warnings = []
def err(msg): errors.append(msg)

pages = sorted(f for f in os.listdir(ROOT) if f.endswith(".html"))
code_files = [os.path.join("assets", f) for f in os.listdir(os.path.join(ROOT, "assets")) if f.endswith((".css", ".js"))]
used = set()

def resolve(ref, base_dir):
    """Turn a reference into a repo-relative path, or None if it isn't a local file."""
    ref = ref.strip()
    if not ref or ref.startswith(("#", "data:", "mailto:", "tel:", "javascript:")):
        return None
    if ref.startswith("/_vercel/"):          # Vercel Analytics / Speed Insights, served by Vercel
        return None
    if ref.startswith(SITE + "/"):
        ref = ref[len(SITE):]
    u = urlparse(ref)
    if u.scheme or u.netloc:
        return None
    path = unquote(u.path)
    if not path:
        return None
    full = os.path.normpath(os.path.join(ROOT, path.lstrip("/")) if path.startswith("/") else os.path.join(ROOT, base_dir, path))
    rel = os.path.relpath(full, ROOT)
    if os.path.isdir(full):
        rel = os.path.join(rel, "index.html")
    elif not os.path.splitext(rel)[1] and os.path.exists(full + ".html"):   # clean URL like /unc
        rel += ".html"
    return rel

ATTR = re.compile(r'\b(?:href|src|poster|data-src|data-poster)\s*=\s*"([^"]*)"', re.I)
OG_IMG = re.compile(r'<meta property="og:image" content="([^"]*)"')
ASSET_STR = re.compile(r"""['"](assets/[^'"]+)['"]""")

for page in pages:
    html = open(os.path.join(ROOT, page), encoding="utf-8").read()
    for ref in ATTR.findall(html):
        if ref.startswith(SITE + "/") and not os.path.exists(os.path.join(ROOT, ref[len(SITE)+1:].split("#")[0] or "index.html")) \
           and not os.path.exists(os.path.join(ROOT, ref[len(SITE)+1:].split("#")[0] + ".html")):
            warnings.append(f"{page}: links to {ref}, which isn't in this site. It will break once the domain points here")
    refs = [r for r in ATTR.findall(html) if not r.startswith(SITE + "/") or r.startswith(SITE + "/assets/")] + ASSET_STR.findall(html) + OG_IMG.findall(html)
    refs += [p.strip().split(" ")[0] for s in re.findall(r'srcset\s*=\s*"([^"]*)"', html) for p in s.split(",")]
    for ref in refs:
        rel = resolve(ref, "")
        if rel is None:
            continue
        if not os.path.exists(os.path.join(ROOT, rel)):
            err(f"{page}: links to {ref}, which doesn't exist")
        used.add(rel)
    for tag in re.findall(r"<img\b[^>]*>", html, re.I):
        if not re.search(r"\balt\s*=", tag):
            err(f"{page}: image without alt text: {tag[:90]}")
    if not re.search(r"<title>[^<]+</title>", html):
        err(f"{page}: missing <title>")
    if page != "404.html" and not re.search(r'<meta name="description" content="[^"]+"', html):
        err(f"{page}: missing meta description")
    if page != "404.html":
        if '<link rel="canonical"' not in html:
            err(f"{page}: missing canonical link (see the <!-- seo --> block in other pages)")
        if not OG_IMG.search(html):
            err(f"{page}: missing og:image link preview (see the <!-- seo --> block in other pages)")
        slug = "/" if page == "index.html" else "/" + page[:-5]
        if os.path.exists(os.path.join(ROOT, "sitemap.xml")) and f"<loc>{SITE}{slug}</loc>" not in open(os.path.join(ROOT, "sitemap.xml")).read():
            err(f"{page}: not listed in sitemap.xml")
    low = html.lower()
    for phrase in BANNED:
        if phrase in low:
            err(f'{page}: uses "{phrase}". Please reword it')

for cf in code_files:
    text = open(os.path.join(ROOT, cf), encoding="utf-8").read()
    base = os.path.dirname(cf)
    if cf.endswith(".css"):
        refs = [r.strip("'\"") for r in re.findall(r"url\(([^)]+)\)", text)]
        for ref in refs:
            rel = resolve(ref, base)
            if rel and not os.path.exists(os.path.join(ROOT, rel)):
                err(f"{cf}: url({ref}) doesn't exist")
            if rel: used.add(rel)
    else:
        for ref in ASSET_STR.findall(text):
            rel = resolve(ref, "")
            if rel and not os.path.exists(os.path.join(ROOT, rel)):
                err(f"{cf}: refers to {ref}, which doesn't exist")
            if rel: used.add(rel)
    for phrase in BANNED:
        if phrase in text.lower():
            err(f'{cf}: uses "{phrase}". Please reword it')

for dirpath, _, files in os.walk(os.path.join(ROOT, "assets")):
    for f in files:
        if f in IGNORE:
            continue
        full = os.path.join(dirpath, f)
        rel = os.path.relpath(full, ROOT)
        mb = os.path.getsize(full) / 1e6
        if mb > MAX_MB:
            err(f"{rel}: {mb:.1f} MB is over the {MAX_MB} MB limit. Compress or resize it")
        if rel not in used and not rel.endswith((".css", ".js")):
            err(f"{rel}: not used by any page. Delete it, or use it")

if warnings:
    print(f"{len(warnings)} warning(s), not blocking:\n")
    for w in warnings:
        print(" - " + w)
    print()
if errors:
    print(f"{len(errors)} problem(s) found:\n")
    for e in errors:
        print(" - " + e)
    sys.exit(1)
print(f"All good: {len(pages)} pages, {len(used)} local files checked.")
