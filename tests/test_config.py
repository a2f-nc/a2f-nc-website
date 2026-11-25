"""vercel.json, sitemap, robots and SEO tags stay consistent with the pages."""
import json, os, re
import pytest
from conftest import ROOT, PAGES

SITE = "https://nc.acts2fellowship.org"
PUBLIC = [p for p in PAGES if p != "404.html"]


def read(name):
    return open(os.path.join(ROOT, name), encoding="utf-8").read()


def slug(page):
    return "/" if page == "index.html" else "/" + page[:-5]


def test_vercel_json_redirects_point_somewhere_real():
    cfg = json.loads(read("vercel.json"))
    assert cfg["cleanUrls"] is True
    for r in cfg["redirects"]:
        src, dst = r["source"], r["destination"]
        assert not os.path.exists(os.path.join(ROOT, src.strip("/") + ".html")), f"redirect {src} hides a real page"
        if dst.startswith("http"):
            continue
        path = dst.split("#")[0]
        target = "index.html" if path == "/" else path.strip("/") + ".html"
        assert os.path.exists(os.path.join(ROOT, target)), f"redirect {src} -> {dst} goes to a missing page"


def test_vercelignore_keeps_private_files_off_the_site():
    ignored = read(".vercelignore").split()
    for name in ["README.md", "CLAUDE.md", "SETUP.md", "tools", "tests", ".github"]:
        assert name in ignored, f"{name} would be published on the website"


def test_sitemap_lists_every_public_page_and_nothing_else():
    locs = re.findall(r"<loc>([^<]+)</loc>", read("sitemap.xml"))
    assert sorted(locs) == sorted(SITE + slug(p) for p in PUBLIC)


def test_robots_points_to_sitemap():
    assert f"Sitemap: {SITE}/sitemap.xml" in read("robots.txt")


@pytest.mark.parametrize("page", PUBLIC)
def test_seo_tags(page):
    html = read(page)
    assert f'<link rel="canonical" href="{SITE}{slug(page)}">' in html
    assert f'<meta property="og:url" content="{SITE}{slug(page)}">' in html
    m = re.search(r'<meta property="og:image" content="([^"]+)"', html)
    assert m and m.group(1).startswith(SITE + "/assets/og/")
    assert os.path.exists(os.path.join(ROOT, m.group(1)[len(SITE) + 1:]))
    desc = re.search(r'<meta name="description" content="([^"]+)"', html).group(1)
    assert 50 <= len(desc) <= 170, f"{page}: description should be 50-170 characters (is {len(desc)})"
    assert "/_vercel/insights/script.js" in html and "/_vercel/speed-insights/script.js" in html


def test_titles_and_descriptions_are_unique():
    titles = [re.search(r"<title>([^<]+)</title>", read(p)).group(1) for p in PUBLIC]
    descs = [re.search(r'<meta name="description" content="([^"]+)"', read(p)).group(1) for p in PUBLIC]
    assert len(set(titles)) == len(titles)
    assert len(set(descs)) == len(descs)


def test_structured_data_is_valid_json():
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', read("index.html"), re.S)
    assert blocks
    data = json.loads(blocks[0])
    types = {n["@type"] for n in data["@graph"]}
    assert {"Organization", "Event"} <= types


def test_shared_header_and_footer_match_on_every_page():
    """The header nav and footer are copied into each page; catch copies that drift apart."""
    def norm(block):
        block = re.sub(r' aria-current="page"', "", block)
        block = re.sub(r'(src|href)="/assets/', r'\1="assets/', block)  # 404.html uses absolute paths
        block = block.replace('="../', '="')  # blog posts sit one folder down
        return re.sub(r'href="/?([a-z-]*)(\.html)?(#\w+)?"', lambda m: f'href="{m.group(1) or "index"}{m.group(3) or ""}"', block)
    navs, foots = {}, {}
    for p in PAGES:
        html = read(p)
        navs[p] = norm(re.search(r'<nav class="topnav".*?</nav>', html, re.S).group(0))
        foots[p] = norm(re.search(r'<footer class="foot">.*?</footer>', html, re.S).group(0))
    assert len(set(navs.values())) == 1, "top nav differs between pages"
    assert len(set(foots.values())) == 1, "footer differs between pages"


def test_no_photo_file_used_on_two_pages():
    seen = {}
    for p in PAGES:
        if p == "404.html":
            continue
        for src in set(re.findall(r"assets/(?:img|vid)/[\w.-]+\.(?:jpg|mp4)", read(p))):
            seen.setdefault(src, []).append(p)
    dupes = {k: v for k, v in seen.items() if len(v) > 1}
    assert dupes == {}, f"photos used on more than one page: {dupes}"
