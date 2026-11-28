#!/usr/bin/env python3
"""Add a blog post to the site, the same way every time (no AI involved).

Given a title, author, the post text (Markdown) and one photo, this:
  - writes blog/<slug>.html, copying the page layout from the newest existing post
  - saves the photo three ways: top of the post, blog-page thumbnail, and the social-share image
  - saves any photos dragged into the post text and points the text at the saved copies
  - puts a card for the post first on blog.html
  - adds the post to sitemap.xml
  - links "Older post" on the new page and "Newer post" on the previous newest page

The "New blog post" issue form feeds it automatically (.github/workflows/new-blog-post.yml).
By hand:  python3 tools/new_post.py --title "My post" --author "Jane Doe" --body post.md --image photo.jpg
Or from an issue's text:  python3 tools/new_post.py --issue-body issue.txt
Needs Pillow (pip install -r requirements-dev.txt) to resize the photos. Nothing else.
"""
import argparse, datetime, html, io, os, re, sys, unicodedata, urllib.error, urllib.parse, urllib.request

SITE = "https://nc.acts2fellowship.org"
GENERIC_ALT = re.compile(r"^(image|img|photo|picture|screenshot.*|.*\.(png|jpe?g|gif|webp|heic))$", re.I)
IMG_MD = re.compile(r"!\[([^\]]*)\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
IMG_HTML = re.compile(r"<img\b[^>]*>", re.I)


class PostError(Exception):
    """Something the person who filled in the form can fix. The message is shown to them."""


# ---------- small helpers ----------

def esc(s):
    return html.escape(s, quote=False)


def attr(s):
    return html.escape(s, quote=True)


def nice_date(d):
    return f"{d:%b} {d.day}, {d.year}"


def make_slug(title):
    s = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"['’]", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if len(s) > 80:
        s = s[:80].rsplit("-", 1)[0]
    if not s:
        raise PostError("The post title needs some letters or numbers in it.")
    return s


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def sub_once(pattern, repl, text, what, flags=re.S):
    new, n = re.subn(pattern, lambda m: repl(m) if callable(repl) else repl, text, count=1, flags=flags)
    if n != 1:
        raise PostError(f"Couldn't find the {what} in the page I copy from. The page layout changed; ask a developer to update tools/new_post.py.")
    return new


# ---------- photos ----------

class _KeepAuthOnlyOnGitHub(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None and "github.com" not in urllib.parse.urlparse(newurl).netloc:
            new.headers.pop("Authorization", None)
        return new


def load_bytes(src):
    """Read a photo from a local path or an https link (GitHub issue attachments)."""
    if os.path.isfile(src):
        with open(src, "rb") as f:
            return f.read()
    if not re.match(r"https://", src):
        raise PostError(f"I couldn't find the photo `{src}`.")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    opener = urllib.request.build_opener(_KeepAuthOnlyOnGitHub)
    last = None
    for headers in ({}, {"Authorization": f"Bearer {token}"} if token else None):
        if headers is None:
            break
        req = urllib.request.Request(src, headers={"User-Agent": "a2f-new-post", **headers})
        try:
            with opener.open(req, timeout=60) as r:
                data = r.read(30_000_001)
            if len(data) > 30_000_000:
                raise PostError("A photo is bigger than 30 MB. Please use a smaller one.")
            return data
        except urllib.error.HTTPError as e:
            last = e
        except urllib.error.URLError as e:
            last = e
    raise PostError(f"I couldn't download a photo from {src} ({last}). Try attaching it again.")


def open_image(data, src):
    try:
        from PIL import Image, ImageOps
    except ImportError:
        raise SystemExit("This needs Pillow: pip install -r requirements-dev.txt")
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception:
        raise PostError(f"`{src}` isn't a picture I can open. Please use a JPG or PNG.")
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, "white")
        bg.paste(img, mask=img.getchannel("A"))
        img = bg
    return img.convert("RGB")


def save_jpeg(img, path, size=None, fit=None):
    from PIL import Image, ImageOps
    img = img.copy()
    if fit:
        img = ImageOps.fit(img, fit, Image.LANCZOS, centering=(0.5, 0.35))
    else:
        img.thumbnail(size or (1600, 1600), Image.LANCZOS)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, "JPEG", quality=84, optimize=True, progressive=True)


def good_alt(alt, fallback):
    alt = (alt or "").strip()
    return fallback if (not alt or GENERIC_ALT.match(alt)) else alt


def find_images(text):
    """Every picture in some Markdown: (full match text, src, alt)."""
    found = []
    for m in IMG_MD.finditer(text):
        found.append((m.group(0), m.group(2), m.group(1)))
    for m in IMG_HTML.finditer(text):
        s = re.search(r'src\s*=\s*["\']([^"\']+)["\']', m.group(0), re.I)
        a = re.search(r'alt\s*=\s*["\']([^"\']*)["\']', m.group(0), re.I)
        if s:
            found.append((m.group(0), s.group(1), a.group(1) if a else ""))
    return found


# ---------- Markdown to HTML (the small subset the posts use) ----------

def inline(text):
    text = esc(text)
    codes = []
    text = re.sub(r"`([^`]+)`", lambda m: codes.append(m.group(1)) or f"\x00{len(codes) - 1}\x00", text)
    text = re.sub(r"!\[([^\]]*)\]\(\s*(?:&lt;)?([^)\s]+?)(?:&gt;)?\s*\)",
                  lambda m: f'<img src="{m.group(2)}" alt="{m.group(1)}" loading="lazy">', text)
    text = re.sub(r"\[([^\]]+)\]\(\s*([^)\s]+)\s*\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*(.+?)\*\*|__(.+?)__", lambda m: f"<strong>{m.group(1) or m.group(2)}</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])|(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])",
                  lambda m: f"<em>{m.group(1) or m.group(2)}</em>", text)
    text = re.sub(r'(?<!["\'=>(])\bhttps?://[^\s<>"]+[^\s<>".,;:!?)]', lambda m: f'<a href="{m.group(0)}">{m.group(0)}</a>', text)
    return re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{codes[int(m.group(1))]}</code>", text)


def to_html(md):
    lines = md.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if m:
            level = min(max(len(m.group(1)), 2), 4)
            out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            i += 1
        elif re.match(r"^\s*([-*_])(\s*\1){2,}\s*$", line):
            out.append("<hr>")
            i += 1
        elif line.lstrip().startswith(">"):
            block = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                block.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append("<blockquote>" + to_html("\n".join(block)) + "</blockquote>")
        elif re.match(r"^\s*([-*+]|\d+[.)])\s+", line):
            ordered = bool(re.match(r"^\s*\d+[.)]\s+", line))
            tag, items = ("ol" if ordered else "ul"), []
            while i < len(lines) and re.match(r"^\s*([-*+]|\d+[.)])\s+", lines[i]):
                items.append(re.sub(r"^\s*([-*+]|\d+[.)])\s+", "", lines[i]))
                i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{inline(t)}</li>" for t in items) + f"</{tag}>")
        else:
            para = []
            while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,6}\s|\s*>|\s*([-*+]|\d+[.)])\s+)", lines[i]):
                para.append(lines[i].strip())
                i += 1
            out.append("<p>" + "<br>\n".join(inline(t) for t in para) + "</p>")
    return "\n".join(out)


def summary_of(md, limit=200):
    for block in re.split(r"\n\s*\n", md.replace("\r\n", "\n")):
        t = IMG_HTML.sub("", IMG_MD.sub("", block))
        t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)
        t = re.sub(r"^\s*(#{1,6}|>|[-*+]|\d+[.)])\s*", "", t, flags=re.M)
        t = re.sub(r"[*_`]", "", t)
        t = " ".join(t.split())
        if len(t) > 3:
            if len(t) <= limit:
                return t
            cut = t[:160].rsplit(" ", 1)[0].rstrip(" ,;:.—-")
            return cut + "…"
    raise PostError("The post needs some text in it.")


# ---------- the site ----------

def newest_post(root):
    """The post whose card is first on blog.html: (slug, title)."""
    blog = read(os.path.join(root, "blog.html"))
    m = re.search(r'<a class="post[^"]*" href="blog/([^"]+)\.html"', blog)
    if not m:
        return None
    slug = m.group(1)
    page = read(os.path.join(root, "blog", slug + ".html"))
    t = re.search(r'<h1 class="t-big">(.*?)</h1>', page, re.S)
    return slug, (t.group(1) if t else slug)


def build_post(root, title, author, body_md, image_src, date=None):
    title, author = " ".join(title.split()), " ".join(author.split())
    if not title:
        raise PostError("The post needs a title.")
    if not author:
        raise PostError("The post needs an author.")
    if not body_md.strip():
        raise PostError("The post needs some text in it.")
    date = date or datetime.date.today()
    slug = make_slug(title)
    if os.path.exists(os.path.join(root, "blog", slug + ".html")):
        raise PostError(f"There is already a post at /blog/{slug}. Pick a different title, or ask Claude to edit that post.")
    prev = newest_post(root)
    if prev is None:
        raise PostError("blog.html has no posts to copy the layout from.")
    prev_slug, prev_title = prev
    template = read(os.path.join(root, "blog", prev_slug + ".html"))

    # photos
    hero_data = load_bytes(image_src)
    hero = open_image(hero_data, image_src)
    n = 1 + max([int(m.group(1)) for f in os.listdir(os.path.join(root, "assets", "blog"))
                 if (m := re.fullmatch(r"post(\d+)\.jpg", f))] or [-1])
    posts_dir = os.path.join(root, "assets", "blog", "posts")
    save_jpeg(hero, os.path.join(posts_dir, slug + ".jpg"))
    save_jpeg(hero, os.path.join(root, "assets", "blog", f"post{n}.jpg"), fit=(720, 540))
    save_jpeg(hero, os.path.join(root, "assets", "og", f"blog-{slug}.jpg"), fit=(1200, 630))

    # photos inside the text
    for k, (whole, src, alt) in enumerate(find_images(body_md), start=1):
        name = f"{slug}-{k}.jpg"
        save_jpeg(open_image(load_bytes(src), src), os.path.join(posts_dir, name))
        md_img = f"![{good_alt(alt, 'A photo from this post')}](../assets/blog/posts/{name})"
        body_md = body_md.replace(whole, md_img, 1)

    hero_alt = good_alt(hero_alt_of(image_src), f"Photo for “{title}”")
    summary = summary_of(body_md)
    body_html = to_html(body_md)

    # the new page, copied from the newest post
    page = template
    page = sub_once(r"<title>.*?</title>", f"<title>{esc(title)} · Acts2Fellowship NC</title>", page, "<title>")
    page = sub_once(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{attr(summary)}">', page, "description")
    page = sub_once(r'(<link rel="canonical" href=")[^"]*(")', lambda m: f"{m.group(1)}{SITE}/blog/{slug}{m.group(2)}", page, "canonical link")
    page = sub_once(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{attr(title)} · Acts2Fellowship NC">', page, "og:title")
    page = sub_once(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{attr(summary)}">', page, "og:description")
    page = sub_once(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{SITE}/blog/{slug}">', page, "og:url")
    page = sub_once(r'<meta property="og:image" content="[^"]*">', f'<meta property="og:image" content="{SITE}/assets/og/blog-{slug}.jpg">', page, "og:image")
    page = sub_once(r'<h1 class="t-big">.*?</h1>', f'<h1 class="t-big">{esc(title)}</h1>', page, "title")
    page = sub_once(r'<p class="byline">.*?</p>', f'<p class="byline">{esc(author)} · <time datetime="{date.isoformat()}">{nice_date(date)}</time></p>', page, "byline")
    page = sub_once(r'<figure class="post-hero">.*?</figure>',
                    f'<figure class="post-hero"><img src="../assets/blog/posts/{slug}.jpg" alt="{attr(hero_alt)}"></figure>', page, "top photo")
    nav = (f'<nav class="post-nav" aria-label="More posts"><a href="{prev_slug}.html"><small>Older post</small>'
           f'<b>{prev_title}</b></a></nav>')
    page = sub_once(r'(<div class="prose post-body">\n).*?\n      </div>\n      <nav class="post-nav".*?</nav>',
                    lambda m: f"{m.group(1)}{body_html}\n      </div>\n      {nav}", page, "post text")
    write(os.path.join(root, "blog", slug + ".html"), page)

    # previous newest post gets a "Newer post" link
    prev_path = os.path.join(root, "blog", prev_slug + ".html")
    prev_page = read(prev_path)
    if "Newer post" not in prev_page:
        newer = f'<a class="nx" href="{slug}.html"><small>Newer post</small><b>{esc(title)}</b></a>'
        prev_page = sub_once(r'(<nav class="post-nav".*?)(</nav>)', lambda m: m.group(1) + newer + m.group(2), prev_page, "older/newer links")
        write(prev_path, prev_page)

    # blog.html card, newest first and "featured"
    blog_path = os.path.join(root, "blog.html")
    blog = read(blog_path)
    blog = blog.replace('<a class="post feature rv"', '<a class="post rv"', 1)
    card = (f'      <a class="post feature rv" href="blog/{slug}.html"><div class="ph"><img src="assets/blog/post{n}.jpg" alt="{attr(hero_alt)}" loading="lazy"></div>'
            f'<div class="bd"><span class="meta">{esc(author)} · {nice_date(date)}</span><h3>{esc(title)}</h3><p>{esc(summary)}</p>'
            f'<span class="go">Read more →</span></div></a>\n')
    blog = sub_once(r'(<div class="wrap posts">\n)', lambda m: m.group(1) + card, blog, "list of posts")
    write(blog_path, blog)

    # sitemap
    sm_path = os.path.join(root, "sitemap.xml")
    lines = read(sm_path).split("\n")
    entry = f"  <url><loc>{SITE}/blog/{slug}</loc></url>"
    blog_idx = [i for i, l in enumerate(lines) if f"<loc>{SITE}/blog/" in l]
    at = next((i for i in blog_idx if re.search(r"/blog/([^<]+)<", lines[i]).group(1) > slug),
              (blog_idx[-1] + 1) if blog_idx else len(lines) - 2)
    lines.insert(at, entry)
    write(sm_path, "\n".join(lines))
    return slug


def hero_alt_of(image_src):
    return getattr(hero_alt_of, "alt", "")


# ---------- reading the issue form ----------

def parse_issue(text):
    parts = re.split(r"^### +(.+?)\s*$", text.replace("\r\n", "\n"), flags=re.M)
    fields = {parts[i].strip().lower(): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}
    fields = {k: ("" if v == "_No response_" else v) for k, v in fields.items()}
    for need, name in [("post title", "Post title"), ("author", "Author"), ("post", "Post"), ("post image", "Post image")]:
        if not fields.get(need):
            raise PostError(f"The **{name}** box is empty.")
    imgs = find_images(fields["post image"])
    src = imgs[0][1] if imgs else (re.search(r"https?://\S+", fields["post image"]) or [None])[0]
    if not src:
        raise PostError("I couldn't find a picture in the **Post image** box. Drag one photo into it.")
    hero_alt_of.alt = imgs[0][2] if imgs else ""
    return fields["post title"], fields["author"], fields["post"], src


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--issue-body", help="a file holding the text of a 'New blog post' issue")
    ap.add_argument("--title")
    ap.add_argument("--author")
    ap.add_argument("--body", help="a file holding the post text (Markdown)")
    ap.add_argument("--image", help="the top photo: a file or an https link")
    ap.add_argument("--alt", default="", help="describe the top photo (optional)")
    ap.add_argument("--date", help="YYYY-MM-DD, default today")
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    a = ap.parse_args(argv)
    try:
        if a.issue_body:
            title, author, body, image = parse_issue(read(a.issue_body))
        elif a.title and a.author and a.body and a.image:
            title, author, body, image = a.title, a.author, read(a.body), a.image
            hero_alt_of.alt = a.alt
        else:
            ap.error("give --issue-body, or all of --title --author --body --image")
        date = datetime.date.fromisoformat(a.date) if a.date else None
        slug = build_post(a.root, title, author, body, image, date)
    except PostError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"slug={slug}")
    print(f"title={' '.join(title.split())}")
    print(f"Added blog/{slug}.html. Review it, then run: python3 tools/check.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
