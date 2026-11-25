"""Shared test setup: serve the repo root on a local port and open it in Chromium.

Run from the repo root:
    pip install -r requirements-dev.txt
    python3 -m playwright install chromium
    python3 -m pytest
Set CHROME_PATH to use an installed Chrome instead of Playwright's Chromium.
"""
import functools, http.server, os, socketserver, threading
import pytest
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = sorted(f for f in os.listdir(ROOT) if f.endswith(".html"))
if os.path.isdir(os.path.join(ROOT, "blog")):  # one page per blog post, served at /blog/<slug>
    PAGES += sorted("blog/" + f for f in os.listdir(os.path.join(ROOT, "blog")) if f.endswith(".html"))
PHONE = {"width": 390, "height": 844}
DESKTOP = {"width": 1280, "height": 900}


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


@pytest.fixture(scope="session")
def base_url():
    handler = functools.partial(_Quiet, directory=ROOT)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        kw = {"executable_path": os.environ["CHROME_PATH"]} if os.environ.get("CHROME_PATH") else {}
        b = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"], **kw)
        yield b
        b.close()


def _new_page(browser, viewport, reduced):
    ctx = browser.new_context(viewport=viewport, reduced_motion="reduce" if reduced else "no-preference",
                              accept_downloads=True)
    # Google Fonts is the only outside request the pages make; keep tests offline and fast.
    ctx.route("**/*", lambda route: route.abort() if not route.request.url.startswith("http://127.0.0.1") else route.continue_())
    page = ctx.new_page()
    page.errors = []
    page.on("pageerror", lambda e: page.errors.append(str(e)))
    page.on("console", lambda m: page.errors.append(m.text) if m.type == "error" and "net::ERR_FAILED" not in m.text and "Failed to load resource" not in m.text else None)
    page.bad_requests = []
    page.on("response", lambda r: page.bad_requests.append(f"{r.status} {r.url}") if r.url.startswith("http://127.0.0.1") and r.status >= 400 and "/_vercel/" not in r.url else None)
    return page


@pytest.fixture
def phone(browser):
    page = _new_page(browser, PHONE, reduced=False)
    yield page
    page.context.close()


@pytest.fixture
def desktop(browser):
    page = _new_page(browser, DESKTOP, reduced=False)
    yield page
    page.context.close()


@pytest.fixture
def phone_reduced(browser):
    page = _new_page(browser, PHONE, reduced=True)
    yield page
    page.context.close()
