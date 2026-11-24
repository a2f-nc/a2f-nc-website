"""The interactive parts of the Stories design."""
import re


def test_pull_up_sheet_opens_switches_and_closes(phone, base_url):
    page = phone
    page.goto(f"{base_url}/index.html")
    sheet = page.locator("#pullup")
    assert sheet.is_hidden()
    page.locator(".tabbar [data-act='pullup']").click()
    sheet.wait_for(state="visible")
    page.wait_for_timeout(100)
    assert page.evaluate("document.activeElement.id") == "pu-h", "focus should move into the sheet"
    assert page.locator("#pullup [data-pane='unc']").is_visible()
    page.locator("#pullup [data-seg='ncsu']").click()
    assert page.locator("#pullup [data-pane='ncsu']").is_visible()
    assert page.locator("#pullup [data-pane='unc']").is_hidden()
    page.keyboard.press("Escape")
    sheet.wait_for(state="hidden")


def test_pull_up_sheet_close_button_and_backdrop(phone, base_url):
    page = phone
    page.goto(f"{base_url}/unc.html")
    page.locator(".topbar [data-act='pullup']").click()
    page.locator("#pullup").wait_for(state="visible")
    page.locator("#pullup .x").click()
    page.locator("#pullup").wait_for(state="hidden")


def test_nc_state_page_opens_nc_state_tab(phone, base_url):
    page = phone
    page.goto(f"{base_url}/nc-state.html")
    page.locator(".tabbar [data-act='pullup']").click()
    page.locator("#pullup").wait_for(state="visible")
    assert page.locator("#pullup [data-pane='ncsu']").is_visible()


def test_add_to_calendar_downloads_weekly_event(phone, base_url, tmp_path):
    page = phone
    page.goto(f"{base_url}/index.html")
    page.locator(".tabbar [data-act='pullup']").click()
    page.locator("#pullup").wait_for(state="visible")
    with page.expect_download() as dl:
        page.locator("#pullup [data-act='ics']").click()
    path = tmp_path / "a.ics"
    dl.value.save_as(path)
    ics = path.read_text()
    assert dl.value.suggested_filename == "a2f-sunday.ics"
    assert "RRULE:FREQ=WEEKLY;BYDAY=SU" in ics
    assert re.search(r"DTSTART;TZID=America/New_York:\d{8}T113000", ics)
    assert "211 W Cameron Ave" in ics
    assert "come as you are" not in ics.lower()


def test_story_ring_opens_viewer_and_keyboard_works(phone, base_url):
    page = phone
    page.goto(f"{base_url}/index.html")
    ring = page.locator(".ring[data-story='feast']")
    ring.click()
    viewer = page.locator(".viewer.open[role='dialog']")
    viewer.wait_for()
    live = viewer.locator(".sr[aria-live]")
    assert live.inner_text().startswith("1 of 2")
    page.keyboard.press("ArrowRight")
    assert live.inner_text().startswith("2 of 2")
    page.keyboard.press("ArrowLeft")
    assert live.inner_text().startswith("1 of 2")
    page.keyboard.press("Escape")
    assert page.locator(".viewer.open").count() == 0
    assert page.evaluate("document.activeElement.dataset.story") == "feast", "focus should return to the ring"
    assert "seen" in ring.get_attribute("class")


def test_story_close_button(phone, base_url):
    page = phone
    page.goto(f"{base_url}/unc.html")
    page.locator(".ring[data-story]").first.click()
    page.locator(".viewer.open").wait_for()
    page.locator(".viewer .cl").click()
    assert page.locator(".viewer.open").count() == 0


def test_every_story_ring_has_slides(phone, base_url):
    for name in ["index.html", "unc.html", "nc-state.html", "our-story.html"]:
        page = phone
        page.goto(f"{base_url}/{name}")
        keys = page.evaluate("[...document.querySelectorAll('[data-story]')].map(r => r.dataset.story)")
        missing = page.evaluate("keys => keys.filter(k => !(window.STORIES && STORIES[k] && STORIES[k].slides.length))", keys)
        assert missing == [], f"{name}: story rings without slides: {missing}"
        bad = page.evaluate("Object.entries(window.STORIES || {}).flatMap(([k, g]) => g.slides.filter(s => !s.alt || !(s.src || s.video)).map(() => k))")
        assert bad == [], f"{name}: slides missing a photo or alt text in {bad}"


def test_story_auto_advances_with_motion(phone, base_url):
    page = phone
    page.goto(f"{base_url}/index.html")
    page.locator(".ring[data-story='feast']").click()
    page.locator(".viewer.open").wait_for()
    page.wait_for_function("document.querySelector('.viewer .sr').textContent.startsWith('2 of 2')", timeout=8000)


def test_story_does_not_auto_advance_with_reduced_motion(phone_reduced, base_url):
    page = phone_reduced
    page.goto(f"{base_url}/index.html")
    page.locator(".ring[data-story='feast']").click()
    page.locator(".viewer.open").wait_for()
    page.wait_for_timeout(6000)
    assert page.locator(".viewer .sr").inner_text().startswith("1 of 2")


def test_hero_story_taps_forward(phone, base_url):
    page = phone
    page.goto(f"{base_url}/index.html")
    hero = page.locator("#hero-story")
    hero.locator(".pp").click()  # pause so it doesn't move on its own
    before = hero.locator(".sr").inner_text()
    hero.locator(".tap.next").click()
    page.wait_for_timeout(350)
    assert hero.locator(".sr").inner_text() != before
    assert hero.locator(".sr").inner_text().startswith("2 of")


def test_reels_render_and_like(phone, base_url):
    page = phone
    page.goto(f"{base_url}/index.html")
    reels = page.locator(".reel[data-src]")
    assert reels.count() > 0
    for i in range(reels.count()):
        r = reels.nth(i)
        assert r.locator("video").count() == 1
        assert r.locator("video").get_attribute("src") == r.get_attribute("data-src")
    like = reels.first.locator(".like")
    like.scroll_into_view_if_needed()
    like.click()
    assert like.get_attribute("aria-pressed") == "true"
    like.click()
    assert like.get_attribute("aria-pressed") == "false"


def test_dm_questions_get_answers(phone_reduced, base_url):
    page = phone_reduced
    page.goto(f"{base_url}/index.html")
    q = page.locator("#dm .qs button").first
    q.scroll_into_view_if_needed()
    question = q.inner_text()
    answer = q.get_attribute("data-a")
    q.click()
    assert q.is_disabled()
    assert page.locator("#dm .bub.me").last.inner_text() == question
    assert page.locator("#dm .bub.them").last.inner_text() == answer


def test_dm_typing_then_answer_with_motion(phone, base_url):
    page = phone
    page.goto(f"{base_url}/index.html")
    q = page.locator("#dm .qs button").nth(1)
    q.scroll_into_view_if_needed()
    q.click()
    page.wait_for_selector("#dm .bub.typing")
    page.wait_for_selector("#dm .bub.typing", state="detached", timeout=3000)
    assert page.locator("#dm .bub.them").last.inner_text() == q.get_attribute("data-a")


def test_swipe_deck_buttons(phone_reduced, base_url):
    page = phone_reduced
    page.goto(f"{base_url}/index.html")
    cards = page.locator("#deck .vcard").count()
    assert cards > 0
    page.locator("#deck-yes").scroll_into_view_if_needed()
    page.locator("#deck-yes").click()
    for _ in range(cards - 1):
        page.locator("#deck-no").click()
    page.wait_for_timeout(100)
    assert page.locator("#deck .vcard").count() == 0
    assert page.locator("#deck .deck-done").is_visible()
    assert page.locator("#picked span").count() == 1


def test_profile_tabs(phone, base_url):
    for name in ["unc.html", "nc-state.html"]:
        page = phone
        page.goto(f"{base_url}/{name}")
        tabs = page.locator(".tabs [role='tab']")
        assert tabs.count() == 3
        tabs.nth(1).click()
        assert tabs.nth(1).get_attribute("aria-selected") == "true"
        assert page.locator("#" + tabs.nth(1).get_attribute("aria-controls")).is_visible()
        assert page.locator("#" + tabs.nth(0).get_attribute("aria-controls")).is_hidden()
        tabs.nth(1).focus()
        page.keyboard.press("ArrowRight")
        assert tabs.nth(2).get_attribute("aria-selected") == "true"
        assert page.evaluate("document.activeElement.getAttribute('role')") == "tab"


def test_photo_lightbox(phone, base_url):
    for name in ["unc.html", "get-connected.html"]:
        page = phone
        page.goto(f"{base_url}/{name}")
        first = page.locator(".feed button").first
        first.scroll_into_view_if_needed()
        first.click()
        lb = page.locator(".lightbox.open")
        lb.wait_for()
        src1 = lb.locator("img").get_attribute("src")
        assert src1.endswith(first.locator("img").get_attribute("src"))
        page.keyboard.press("ArrowRight")
        assert lb.locator("img").get_attribute("src") != src1
        page.keyboard.press("Escape")
        assert page.locator(".lightbox.open").count() == 0


def test_statement_of_faith_has_all_beliefs_with_references(phone, base_url):
    page = phone
    page.goto(f"{base_url}/statement-of-faith.html")
    beliefs = page.locator("article.belief")
    assert beliefs.count() == 9
    for i in range(9):
        refs = beliefs.nth(i).locator(".refs a[href*='biblegateway.com']")
        assert refs.count() >= 1
    assert page.locator("#sofnav a").count() == 9


def test_get_connected_embeds_form(phone, base_url):
    page = phone
    page.goto(f"{base_url}/get-connected.html")
    src = page.locator(".formcard iframe").get_attribute("src")
    assert src.startswith("https://docs.google.com/forms/") and "embedded=true" in src
