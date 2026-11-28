"""tools/new_post.py builds a blog post from the "New blog post" issue form, the same way every time."""
import importlib.util, os, shutil, subprocess, sys

import pytest
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("new_post", os.path.join(ROOT, "tools", "new_post.py"))
new_post = importlib.util.module_from_spec(spec)
spec.loader.exec_module(new_post)

BODY = """Hello **world**, this is a *test* with a [link](https://example.com).
Second line.

## A heading

### A smaller heading

- one
- two

![Image]({inline})

![Image]({inline})

Last paragraph.
"""


def issue(author="Jane Doe", body="Hi there.", image="![Sunday lunch](https://github.com/user-attachments/assets/abc)"):
    return f"### Author\n\n{author}\n\n### Post\n\n{body}\n\n### Post image\n\n{image}\n"


def run(site, *args):
    return subprocess.run([sys.executable, str(site / "tools" / "new_post.py"), *args], capture_output=True, text=True, cwd=site)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    site = tmp_path_factory.mktemp("site") / "site"
    shutil.copytree(ROOT, site, ignore=shutil.ignore_patterns(".git", "tests", "__pycache__", ".pytest_cache"))
    pics = tmp_path_factory.mktemp("pics")
    Image.new("RGB", (2000, 1500), (200, 120, 60)).save(pics / "hero.jpg")
    Image.new("RGB", (800, 600), (60, 120, 200)).save(pics / "inline.png")
    (pics / "post.md").write_text(BODY.format(inline=pics / "inline.png"))
    before = (site / "blog.html").read_text()
    first = [l for l in before.splitlines() if 'class="post feature rv"' in l][0]
    old_slug = first.split('href="blog/')[1].split(".html")[0]
    r = run(site, "--title", "Why I Love Chapel Hill's Sundays", "--author", "Jane Doe", "--body", str(pics / "post.md"),
            "--image", str(pics / "hero.jpg"), "--alt", "Sunday lunch with friends", "--date", "2026-11-30")
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
    import re
    desc = re.search(r'<meta name="description" content="([^"]+)"', page).group(1)
    assert 50 <= len(desc) <= 170, desc  # the site's SEO test requires this range
    import re
    desc = re.search(r'<meta name="description" content="([^"]+)"', page).group(1)
    assert 50 <= len(desc) <= 170, desc  # the site's SEO test requires this range
    assert '<img src="../assets/blog/posts/why-i-love-chapel-hills-sundays-1.jpg"' in page
    assert page.count("why-i-love-chapel-hills-sundays-1.jpg") == 2 and "sundays-2.jpg" not in page  # same photo twice, saved once
    assert "<h3>A smaller heading</h3>" in page
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
    r = run(site, "--title", "Why I Love Chapel Hill's Sundays", "--author", "A", "--body", str(pics / "post.md"), "--image", str(pics / "hero.jpg"))
    assert r.returncode == 1 and "already a post" in r.stderr


def test_empty_boxes_are_explained(tmp_path):
    f = tmp_path / "i.txt"
    f.write_text(issue(author="_No response_"))
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "new_post.py"), "--issue-body", str(f), "--issue-title", "Hi"], capture_output=True, text=True)
    assert r.returncode == 1 and "**Author** box is empty" in r.stderr


def test_markdown_and_summary():
    assert new_post.to_html("a\nb\n\n1. x\n2. y") == "<p>a<br>\nb</p>\n<ol><li>x</li><li>y</li></ol>"
    assert new_post.to_html("<script>x</script>") == "<p>&lt;script&gt;x&lt;/script&gt;</p>"
    assert new_post.to_html("# Big") == "<h2>Big</h2>"
    assert new_post.summary_of("![i](x.png)\n\nShort **intro** here. It keeps going for a little while.\n\nMore.") == "Short intro here. It keeps going for a little while."
    long = new_post.summary_of("word " * 80)
    assert long.endswith("\u2026") and len(long) <= 170
    assert 50 <= len(new_post.summary_of("x" * 190 + " tail")) <= 170
    tiny = new_post.summary_of("> Hi from Chapel Hill\nJon Lee", "Jon Lee")  # too short: gets a lead-in so it stays 50-170 characters
    assert tiny.startswith("Hi from Chapel Hill Jon Lee") and 50 <= len(tiny) <= 170
    assert 50 <= len(new_post.summary_of("One.\n\nTwo short paragraphs that together are long enough.")) <= 170
    assert new_post.make_slug("How Tacos Changed My College Life!") == "how-tacos-changed-my-college-life"


def test_headings_inside_the_post_do_not_cut_it_off():
    t, a, body, img, alt = new_post.parse_issue(issue(body="Intro\n\n### Tips\n\nMore text\n\n### Author\n\nsneaky"), "A title")
    assert t == "A title" and a == "Jane Doe" and "More text" in body and body.endswith("sneaky") and alt == "Sunday lunch"
    assert img == "https://github.com/user-attachments/assets/abc"


def test_quotes_and_bad_links_cannot_inject_html():
    h = new_post.to_html('[a](https://e.com/"onmouseover="x) [b](javascript:alert`1`) ![z" onerror="y](https://e.com/p.png) ![ok](../assets/blog/posts/a.jpg)')
    assert '"onmouseover' not in h and 'onerror="' not in h and "javascript:" not in h.replace("javascript:alert", "")
    assert 'href="javascript' not in h and "<img src=\"https://" not in h
    assert '<img src="../assets/blog/posts/a.jpg" alt="ok"' in h
    assert new_post.to_html("`x \x00 y`").count("\x00") == 0


def test_only_github_hosts_get_the_token_or_are_fetched():
    ok = new_post.is_github_host
    assert ok("https://github.com/user-attachments/assets/1") and ok("https://private-user-images.githubusercontent.com/1.png")
    for bad in ["https://github.com.evil.io/x", "https://evil-github.com/x", "http://github.com/x", "https://evilgithubusercontent.com/x", "https://example.com/p.png"]:
        assert not ok(bad), bad
    with pytest.raises(new_post.PostError):
        new_post.load_bytes("https://example.com/p.png")
    with pytest.raises(new_post.PostError):
        new_post.load_bytes("/etc/passwd")  # local files only when run by hand


def test_issue_with_a_photo_link_to_another_site_is_refused(built):
    site, _, _, pics = built
    f = pics / "bad.txt"
    f.write_text(issue(image="https://example.com/p.png"))
    r = run(site, "--issue-body", str(f), "--issue-title", "Another post")
    assert r.returncode == 1 and "attached to the issue" in r.stderr


def test_the_default_issue_title_is_not_accepted_as_a_post_title():
    with pytest.raises(new_post.PostError, match="Replace"):
        new_post.parse_issue(issue(), "Post title")
    with pytest.raises(new_post.PostError, match="Replace"):
        new_post.parse_issue(issue(), "  ")
