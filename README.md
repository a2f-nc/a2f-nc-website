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
| `blog.html` | Blog post list (posts themselves are still on the old site, see SETUP.md) |
| `404.html` | Shown for any page that doesn't exist |

Some page text lives in a `<script>` block near the bottom of each page (`window.STORIES = {...}`).
That's where each story's slides, captions and photos are listed.

## Folders

| Path | What it is |
|---|---|
| `assets/img/` | Photos, about 1080px on the long side |
| `assets/vid/` | Reel clips (720x1280 MP4, about 1 MB each) plus a `.jpg` poster frame with the same name |
| `assets/people/` | Student council and Ben & Helen headshots, ministry logos |
| `assets/blog/` | Blog post thumbnails |
| `assets/sym/`, `assets/brand/` | Campus symbols, A2F tree icon |
| `assets/fonts/` | Glacial Indifference (brand font, self-hosted) |
| `tools/check.py` | The site check that also runs on every pull request |

## Adding a photo or clip

- Photos: resize to about 1080px on the long side, keep it under about 400 KB, and save as `.jpg` in `assets/img/`.
- Clips: 720x1280 H.264 MP4 under about 2 MB, plus a poster `.jpg` with the same name, in `assets/vid/`.
- Use a new file name when you replace a photo (photos are cached for a week).
- Every photo needs a short `alt` description for screen readers, and each photo should only appear once on the site.
- Delete files you stop using. The check fails if something in `assets/` isn't used.
