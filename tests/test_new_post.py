"""tools/new_post.py builds a blog post from the "New blog post" issue form, the same way every time."""
import importlib.util, os, shutil, subprocess, sys

import pytest
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("new_post", os.path.join(ROOT, "tools", "new_post.py"))
new_post = importlib.util.module_from_spec(spec)
spec.loader.exec_module(new_post)

ISSUE = """### Post title

Why I Love Chapel Hill's Sundays

### Author

Jane Doe

### Post

Hello **world**, this is a *test* with a [link](https://example.com).
Second line.

## A heading

- one
- two

![Image]({inline})

Last paragraph.

### Post image

![Sunday lunch with friends]({hero})
"""


def run(site, *args):
    return subprocess.run([sys.executable, str(site / "tools" / "new_post.py"), *args], capture_output=True, text=True, cwd=site)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    site = tmp_path_factory.mktemp("site") / "site"
    shutil.copytree(ROOT, site, ignore=shutil.ignore_patterns(".git", "tests", "__pycache__", ".pytest_cache"))
    pics = tmp_path_factory.mktemp("pics")
    Image.new("RGB", (2000, 1500), (200, 120, 60)).save(pics / "hero.jpg")
    Image.new("RGB", (800, 600), (60, 120, 200)).save(pics / "inline.png")
    (pics / "issue.txt").write_text(ISSUE.format(hero=pics / "hero.jpg", inline=pics / "inline.png"))
    before = (site / "blog.html").read_text()
    first = [l for l in before.splitlines() if 'class="post feature rv"' in l][0]
    old_slug = first.split('href="blog/')[1].split(".html")[0]
    r = run(site, "--issue-body", str(pics / "issue.txt"), "--date", "2026-11-30")
    return site, r, old_slug, pics


def test_script_succeeds_and_check_passes(built):
    site, r, _, _ = built
    assert r.returncode == 0, r.stderr
    assert "slug=why-i-love-chapel-hills-sundays" in r.stdout
    c = subprocess.run([sys.executable, "-I", str(site / "tools" / "check.py")], capture_output=True, text=True, cwd=site)
    assert c.returncode == 0, c.stdout


def test_page_has_title_byline_text_and_photos(built):
    site = built[0]
    page = (site / "blog" / "why-i-love-chapel-hills-sundays.html").read_text()
    assert '<h1 class="t-big">Why I Love Chapel Hill\'s Sundays</h1>' in page
    assert 'Jane Doe · <time datetime="2026-11-30">Nov 30, 2026</time>' in page
    assert "<strong>world</strong>" in page and "<em>test</em>" in page and '<a href="https://example.com">link</a>' in page
    assert "<h2>A heading</h2>" in page and "<ul><li>one</li><li>two</li></ul>" in page
    assert 'alt="Sunday lunch with friends"' in page
    assert '<img src="../assets/blog/posts/why-i-love-chapel-hills-sundays-1.jpg"' in page
    assert '<link rel="canonical" href="https://nc.acts2fellowship.org/blog/why-i-love-chapel-hills-sundays">' in page
    for f in ["assets/blog/posts/why-i-love-chapel-hills-sundays.jpg", "assets/blog/posts/why-i-love-chapel-hills-sundays-1.jpg",
              "assets/blog/post9.jpg", "assets/og/blog-why-i-love-chapel-hills-sundays.jpg"]:
        assert (site / f).exists(), f
    assert Image.open(site / "assets/og/blog-why-i-love-chapel-hills-sundays.jpg").size == (1200, 630)
    assert Image.open(site / "assets/blog/post9.jpg").size == (720, 540)


def test_links_go_both_ways(built):
    site, _, old_slug, _ = built
    new = (site / "blog" / "why-i-love-chapel-hills-sundays.html").read_text()
    assert f'href="{old_slug}.html"><small>Older post' in new and "Newer post" not in new
    old = (site / "blog" / f"{old_slug}.html").read_text()
    assert 'class="nx" href="why-i-love-chapel-hills-sundays.html"><small>Newer post' in old


def test_blog_list_and_sitemap(built):
    site, _, old_slug, _ = built
    cards = [l for l in (site / "blog.html").read_text().splitlines() if l.lstrip().startswith('<a class="post')]
    assert 'href="blog/why-i-love-chapel-hills-sundays.html"' in cards[0] and "feature" in cards[0]
    assert "feature" not in cards[1] and f"blog/{old_slug}.html" in cards[1]
    assert sum("feature" in c for c in cards) == 1
    sm = (site / "sitemap.xml").read_text()
    assert sm.count("/blog/why-i-love-chapel-hills-sundays<") == 1


def test_same_title_again_is_refused(built):
    site, _, _, pics = built
    r = run(site, "--issue-body", str(pics / "issue.txt"))
    assert r.returncode == 1 and "already a post" in r.stderr


def test_empty_boxes_are_explained(tmp_path):
    f = tmp_path / "i.txt"
    f.write_text("### Post title\n\nHi\n\n### Author\n\n_No response_\n\n### Post\n\nText\n\n### Post image\n\nx")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "new_post.py"), "--issue-body", str(f)], capture_output=True, text=True)
    assert r.returncode == 1 and "**Author** box is empty" in r.stderr


def test_markdown_and_summary():
    assert new_post.to_html("a\nb\n\n1. x\n2. y") == "<p>a<br>\nb</p>\n<ol><li>x</li><li>y</li></ol>"
    assert new_post.to_html("<script>x</script>") == "<p>&lt;script&gt;x&lt;/script&gt;</p>"
    assert new_post.to_html("# Big") == "<h2>Big</h2>"
    assert new_post.summary_of("![i](x.png)\n\nShort **intro** here.\n\nMore.") == "Short intro here."
    long = new_post.summary_of("word " * 80)
    assert long.endswith("…") and len(long) <= 162
    assert new_post.make_slug("How Tacos Changed My College Life!") == "how-tacos-changed-my-college-life"
