"""Every page: loads cleanly, fits a phone screen, and has the shared pieces."""
import pytest
from conftest import PAGES

NO_OVERFLOW = "document.documentElement.scrollWidth <= window.innerWidth + 1"


@pytest.mark.parametrize("name", PAGES)
@pytest.mark.parametrize("size", ["phone", "desktop"])
def test_page_loads_cleanly(request, base_url, name, size):
    page = request.getfixturevalue(size)
    resp = page.goto(f"{base_url}/{name}", wait_until="load")
    assert resp.status == 200
    # scroll through so lazy images and reveal animations kick in
    page.evaluate("""async () => { for (let y = 0; y < document.body.scrollHeight; y += 600) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 30)); } window.scrollTo(0, 0); }""")
    page.wait_for_timeout(300)
    assert page.errors == [], f"JavaScript errors on {name}: {page.errors}"
    assert page.bad_requests == [], f"Missing files on {name}: {page.bad_requests}"
    assert page.evaluate(NO_OVERFLOW), f"{name} scrolls sideways at {size} width"
    broken = page.evaluate("[...document.images].filter(i => i.complete && i.naturalWidth === 0 && i.getAttribute('src')).map(i => i.getAttribute('src'))")
    assert broken == [], f"Broken images on {name}: {broken}"


@pytest.mark.parametrize("name", PAGES)
def test_page_has_shared_layout(phone, base_url, name):
    page = phone
    page.goto(f"{base_url}/{name}")
    assert page.locator("h1").count() == 1, "each page needs exactly one main heading"
    assert page.locator("a.sr[href='#main']").count() == 1, "skip link missing"
    assert page.locator("main#main").count() == 1
    assert page.locator("header.topbar").count() == 1
    assert page.locator("footer.foot").count() == 1
    assert page.locator("nav.tabbar").is_visible(), "mobile tab bar should show at phone width"
    assert page.locator("#pullup").count() == 1, "Pull up sheet missing"
    assert page.title().strip()


@pytest.mark.parametrize("name", PAGES)
def test_skip_link_is_first_tab_stop(phone, base_url, name):
    phone.goto(f"{base_url}/{name}")
    phone.keyboard.press("Tab")
    assert phone.evaluate("document.activeElement.getAttribute('href')") == "#main"


def test_desktop_nav_marks_current_page(desktop, base_url):
    for name, label in [("index.html", "Home"), ("unc.html", "UNC"), ("nc-state.html", "NC State"), ("our-story.html", "About"), ("blog.html", "Blog")]:
        desktop.goto(f"{base_url}/{name}")
        current = desktop.locator(".topnav [aria-current='page']")
        assert current.count() == 1 and current.inner_text().strip() == label


def test_reduced_motion_shows_everything_without_animation(phone_reduced, base_url):
    page = phone_reduced
    page.goto(f"{base_url}/index.html")
    assert not page.evaluate("document.documentElement.classList.contains('motion')")
    hidden = page.evaluate("[...document.querySelectorAll('.rv')].filter(e => !e.classList.contains('in')).length")
    assert hidden == 0
    # reels must not autoplay
    page.locator("#reels").scroll_into_view_if_needed()
    page.wait_for_timeout(500)
    assert page.evaluate("[...document.querySelectorAll('.reel video')].every(v => v.paused)")


def test_404_page_works_at_any_depth(phone, base_url):
    # Vercel serves 404.html for any missing URL, so it must only use absolute paths
    html = open(__import__("conftest").ROOT + "/404.html", encoding="utf-8").read()
    import re
    rel = [r for r in re.findall(r'(?:href|src)="([^"]+)"', html) if not r.startswith(("/", "#", "http", "mailto:"))]
    assert rel == [], f"404.html has relative links that break at nested URLs: {rel}"
    phone.goto(f"{base_url}/404.html")
    assert phone.bad_requests == []
