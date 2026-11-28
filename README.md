# Acts2Fellowship NC website

The website for Acts2Fellowship at UNC and NC State, in the "Stories" design: story rings,
tap-through stories, reels, a swipe card deck, a DM-style FAQ and campus "profile" pages.
It's a plain static site (HTML, CSS and a little JavaScript, no framework and no build step), hosted on Vercel.

- Every pull request gets its own preview link from Vercel, posted as a comment on the PR.
- Merging into `main` publishes the live site automatically.
- First-time setup of GitHub and Vercel is in [SETUP.md](SETUP.md).

## Making a change

1. Edit the page you want directly (for example `unc.html`). Styles are in `assets/c2.css`,
   behavior (stories, reels, swipe deck, Pull up sheet) is in `assets/c2.js`.
2. Preview locally: `python3 -m http.server 8000`, then open http://localhost:8000
   (use your browser's phone view at 390px wide too).
3. Run the check: `python3 tools/check.py`. It should say "All good".
   Optionally run the tests too (they also run automatically on every pull request):
   `pip install -r requirements-dev.txt`, `python3 -m playwright install chromium`, then `python3 -m pytest`.
4. Push a branch and open a pull request. Check the Vercel preview link on the PR (on your phone too), then ask for a review.

## Pages

| Page | What it is |
|---|---|
| `index.html` | Home: story rings, intro story, Sunday ticket, campus picker, reels, swipe deck, feed, events, DMs (FAQ) |
| `unc.html` | UNC "profile" (@a2f_unc): highlights, Posts / Reels / Events tabs, student council |
| `nc-state.html` | NC State "profile" (@a2fncsu), same pattern in maroon |
| `our-story.html` | How A2F started, with a tap-through timeline story |
| `leadership.html` | Ben and Helen (Q&A as chat threads) and our mentors |
| `statement-of-faith.html` | What we believe, with Bible references |
| `get-connected.html` | The UNC get-connected form, NC State sign-up link, photo grid |
| `other-ministries.html` | ISMP and Area Youth Ministry |
| `blog.html` | Blog post list |
| `blog/*.html` | One page per blog post. The file name matches the post's old Squarespace address |
| `404.html` | Shown for any page that doesn't exist |

To add a blog post: open a new issue on GitHub and pick **New blog post**. Fill in the title, author, the post (you can format it and
drag photos in) and one photo. A workflow builds the page, the blog list card, the sitemap entry and the older/newer links
with `tools/new_post.py` and opens a pull request with a preview. Reply on the issue to ask for changes, then merge the pull request.
By hand, the same thing is `python3 tools/new_post.py --title "..." --author "..." --body post.md --image photo.jpg` (needs `pip install -r requirements-dev.txt`).
Pages in `blog/` are one folder down, so their links start with `../` (for example `../assets/c2.css`).

Some page text lives in a `<script>` block near the bottom of each page (`window.STORIES = {...}`).
That's where each story's slides, captions and photos are listed.

## Folders

| Path | What it is |
|---|---|
| `assets/img/` | Photos, about 1080px on the long side |
| `assets/vid/` | Reel clips (720x1280 MP4, about 1 MB each) plus a `.jpg` poster frame with the same name |
| `assets/people/` | Student council and Ben & Helen headshots, ministry logos |
| `assets/blog/` | Blog card thumbnails (`postN.jpg`) and the photo at the top of each post (`posts/`) |
| `assets/sym/`, `assets/brand/` | Campus symbols, A2F tree icon |
| `assets/fonts/` | Glacial Indifference (brand font, self-hosted) |
| `tools/check.py` | The site check that also runs on every pull request |
| `tests/` | Automated tests: every page in a real browser at phone and desktop size, plus the interactive features |

## Adding a photo or clip

- Photos: resize to about 1080px on the long side, keep it under about 400 KB, and save as `.jpg` in `assets/img/`.
- Clips: 720x1280 H.264 MP4 under about 2 MB, plus a poster `.jpg` with the same name, in `assets/vid/`.
- Use a new file name when you replace a photo (photos are cached for a week).
- Every photo needs a short `alt` description for screen readers, and each photo should only appear once on the site.
- Delete files you stop using. The check fails if something in `assets/` isn't used.

## Tests

Every pull request runs two jobs on GitHub ("Check site"):

- **check**: `tools/check.py`: broken links, missing alt text, titles, descriptions, SEO tags, sitemap, file sizes, unused files, banned copy.
- **test**: `python -m pytest` opens every page in Chromium at phone (390px) and desktop width and checks that:
  - pages load with no script errors or missing files, and nothing scrolls sideways
  - stories open, move with arrow keys and taps, close with Esc, and don't auto-advance with "reduce motion" on
  - the Pull up sheet opens, switches UNC / NC State and closes; "Add to my calendar" downloads a weekly Sunday event
  - reels, the swipe deck, the DM questions, profile tabs and the photo lightbox work
  - header and footer are the same on every page, no photo is on two pages, redirects and sitemap are consistent
  - `tools/check.py` itself catches each kind of problem

If a test fails, the PR shows a red ✗ with the reason. Fix the page (not the test) unless the change was intentional.
