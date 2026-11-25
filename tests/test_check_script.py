"""tools/check.py catches the problems it promises to catch."""
import os, shutil, subprocess, sys, textwrap
import pytest
from conftest import ROOT

GOOD_PAGE = textwrap.dedent("""\
    <!doctype html><html><head><title>T</title>
    <meta name="description" content="A good page description.">
    <link rel="canonical" href="https://nc.acts2fellowship.org/">
    <meta property="og:image" content="https://nc.acts2fellowship.org/assets/og/home.jpg">
    <link rel="stylesheet" href="assets/c2.css"></head>
    <body><img src="assets/img/a.jpg" alt="Friends on the quad"><a href="index.html">home</a></body></html>""")


@pytest.fixture
def site(tmp_path):
    os.makedirs(tmp_path / "tools")
    os.makedirs(tmp_path / "assets" / "img")
    os.makedirs(tmp_path / "assets" / "og")
    os.makedirs(tmp_path / "blog")
    shutil.copy(os.path.join(ROOT, "tools", "check.py"), tmp_path / "tools" / "check.py")
    (tmp_path / "assets" / "c2.css").write_text("body{}")
    (tmp_path / "assets" / "img" / "a.jpg").write_bytes(b"jpg")
    (tmp_path / "assets" / "og" / "home.jpg").write_bytes(b"jpg")
    (tmp_path / "index.html").write_text(GOOD_PAGE)
    (tmp_path / "sitemap.xml").write_text("<loc>https://nc.acts2fellowship.org/</loc>")
    return tmp_path


def run(site):
    r = subprocess.run([sys.executable, "-I", str(site / "tools" / "check.py")], capture_output=True, text=True)
    return r.returncode, r.stdout


def test_clean_site_passes(site):
    code, out = run(site)
    assert code == 0, out
    assert "All good" in out


def test_the_real_site_passes():
    r = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "check.py")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


@pytest.mark.parametrize("change, expected", [
    (lambda s: s.replace('alt="Friends on the quad"', ""), "image without alt text"),
    (lambda s: s.replace('href="index.html"', 'href="missing.html"'), "missing.html, which doesn't exist"),
    (lambda s: s.replace("<title>T</title>", ""), "missing <title>"),
    (lambda s: s.replace('<meta name="description" content="A good page description.">', ""), "missing meta description"),
    (lambda s: s.replace("</body>", "Come as you are!</body>"), 'uses "come as you are"'),
    (lambda s: s.replace('<link rel="canonical" href="https://nc.acts2fellowship.org/">', ""), "missing canonical"),
    (lambda s: s.replace('<meta property="og:image" content="https://nc.acts2fellowship.org/assets/og/home.jpg">', ""), "missing og:image"),
])
def test_page_problems_are_caught(site, change, expected):
    p = site / "index.html"
    p.write_text(change(p.read_text()))
    code, out = run(site)
    assert code == 1
    assert expected in out


def test_unused_asset_is_caught(site):
    (site / "assets" / "img" / "extra.jpg").write_bytes(b"jpg")
    code, out = run(site)
    assert code == 1 and "extra.jpg: not used" in out


def test_oversized_asset_is_caught(site):
    (site / "assets" / "img" / "a.jpg").write_bytes(b"0" * 6_000_000)
    code, out = run(site)
    assert code == 1 and "over the 5 MB limit" in out


def test_page_missing_from_sitemap_is_caught(site):
    (site / "about.html").write_text(GOOD_PAGE.replace('href="https://nc.acts2fellowship.org/"', 'href="https://nc.acts2fellowship.org/about"'))
    code, out = run(site)
    assert code == 1 and "about.html: not listed in sitemap.xml" in out


def test_links_to_old_site_only_warn(site):
    p = site / "index.html"
    p.write_text(p.read_text().replace("</body>", '<a href="https://nc.acts2fellowship.org/blog/old-post">x</a></body>'))
    code, out = run(site)
    assert code == 0
    assert "will break once the domain points here" in out


def test_blog_post_links_resolve_from_its_folder(site):
    post = GOOD_PAGE.replace('href="https://nc.acts2fellowship.org/"', 'href="https://nc.acts2fellowship.org/blog/hello"')
    post = post.replace('"assets/', '"../assets/').replace('href="index.html"', 'href="../index.html"')
    (site / "blog" / "hello.html").write_text(post)
    (site / "sitemap.xml").write_text("<loc>https://nc.acts2fellowship.org/</loc><loc>https://nc.acts2fellowship.org/blog/hello</loc>")
    code, out = run(site)
    assert code == 0, out
    (site / "blog" / "hello.html").write_text(post.replace('href="../index.html"', 'href="index.html"'))
    code, out = run(site)
    assert code == 1 and "blog/hello.html" in out and "doesn't exist" in out
