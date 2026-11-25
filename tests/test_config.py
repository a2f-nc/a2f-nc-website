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


def test_vercel_skips_builds_only_for_files_that_are_not_the_website():
    import subprocess, tempfile
    cfg = json.loads(read("vercel.json"))
    assert "tools/vercel-ignore.sh" in cfg["ignoreCommand"] and cfg["ignoreCommand"].endswith("|| exit 1")
    script = os.path.join(ROOT, "tools", "vercel-ignore.sh")

    def run(env_sha, d, **extra):
        env = {k: v for k, v in os.environ.items() if not k.startswith("VERCEL_")}
        if env_sha:
            env["VERCEL_GIT_PREVIOUS_SHA"] = env_sha
        env.update(extra)
        return subprocess.run(["bash", script], cwd=d, env=env, capture_output=True).returncode

    with tempfile.TemporaryDirectory() as d:
        def git(*a):
            return subprocess.run(["git", "-c", "user.email=a@b", "-c", "user.name=a", *a], cwd=d, check=True, capture_output=True, text=True).stdout.strip()
        def commit(path):
            os.makedirs(os.path.dirname(os.path.join(d, path)) or d, exist_ok=True)
            open(os.path.join(d, path), "a").write("x\n")
            git("add", "-A"); git("commit", "-qm", path)
            return git("rev-parse", "HEAD")
        git("init", "-q")
        base = commit("index.html")
        commit(".github/workflows/x.yml"); commit("tests/t.py"); commit("README.md")
        assert run(base, d) == 0, "workflow, test and doc changes should skip the build"
        for site_file in ["unc.html", "assets/c2.css", "vercel.json", "assets/img/a.jpg", "sitemap.xml"]:
            prev = git("rev-parse", "HEAD")
            commit(site_file)
            assert run(prev, d) == 1, f"{site_file} must still deploy"
        commit("README.md")
        assert run(None, d) == 0, "no previous commit known: compare with the commit before (a docs-only last commit skips)"
        assert run(None, d, VERCEL_GIT_COMMIT_REF="main") == 1, "the live site never guesses: build"
        assert run(None, d, VERCEL_ENV="production") == 1, "the live site never guesses: build"
        commit("assets/c2.js")
        assert run(None, d) == 1, "no previous commit known and a site file changed: build"
        assert run(git("rev-parse", "HEAD"), d) == 1, "nothing changed since the previous commit: build"
        assert run("deadbeef", d) == 1, "unusable previous commit: build"


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


def test_dependabot_only_auto_merges_after_check_and_test():
    """Dependabot pull requests may merge themselves, but only once both CI jobs pass, and never a major bump."""
    wf = read(".github/workflows/check-site.yml")
    job = wf.split("dependabot-automerge:", 1)[1]
    assert "needs: [check, test]" in job
    assert "dependabot[bot]" in job and "gh pr merge --auto" in job
    assert "semver-major" not in job
    cfg = read(".github/dependabot.yml")
    assert cfg.count("update-types: [minor, patch]") == 2, "grouped monthly updates must leave out major versions"
    assert cfg.count("applies-to: security-updates") == 2




def _jobs(wf):
    """Split a workflow file into {job name: job text} without needing a YAML library."""
    body = wf.split("\njobs:\n", 1)[1]
    return dict(re.findall(r"^  ([\w-]+):\n(.*?)(?=^  [\w-]+:\n|\Z)", body, re.S | re.M))


@pytest.mark.parametrize("name", ["claude.yml", "issue-preview-link.yml", "check-claude-signin.yml"])
def test_claude_workflows_are_read_only_by_default(name):
    top = read(".github/workflows/" + name).split("\njobs:\n", 1)[0]
    assert top.split("\npermissions:\n", 1)[1].strip() == "contents: read", "workflow default must stay read-only"


def test_claude_only_starts_without_mention_for_the_team():
    """New issues and issue comments start Claude without @claude, but only for people GitHub ties to the repo,
    never for bots, and the Claude action's own write-access check stays on."""
    wf = read(".github/workflows/claude.yml")
    assert "allowed_non_write_users" not in wf, "the action's own write-access check must stay on"
    jobs = _jobs(wf)
    team = "contains(fromJSON('[\"OWNER\",\"MEMBER\",\"COLLABORATOR\",\"CONTRIBUTOR\"]')"
    for line in jobs["claude"].split("if: |", 1)[1].split("runs-on:", 1)[0].splitlines():
        if "||" in line or "(github" in line:
            assert "@claude" in line or "label.name == 'claude'" in line or (team in line and "author_association" in line), \
                f"this trigger needs @claude, the label, or a team author: {line.strip()}"
    feedback = jobs["issue-feedback"].split("runs-on:", 1)[0]
    assert team in feedback and "comment.author_association" in feedback, "issue feedback must come from the team"
    assert "user.type != 'Bot'" in feedback, "Claude must not answer its own or other bots' comments"
    assert "!github.event.issue.pull_request" in feedback
    prompt = [l for l in jobs["claude"].splitlines() if l.strip().startswith("prompt:")]
    assert len(prompt) == 1 and "github.event.action == 'opened'" in prompt[0], "that prompt must only apply to new issues"


def test_feedback_only_pushes_to_the_issues_own_pull_request():
    job = _jobs(read(".github/workflows/claude.yml"))["issue-feedback"]
    assert 'startswith(\\"claude/issue-$ISSUE-\\")' in job, "must look up the PR for this issue's own branch"
    assert "ref: ${{ steps.find.outputs.sha" in job, "check out the exact commit, not a branch name that can move"
    assert "isCrossRepository == false" in job, "never check out a branch from a fork"
    assert "Bash(git push origin HEAD)" in job and "Bash(git push:" not in job, "only a plain push of the checked-out branch"
    assert "Bash(git checkout" not in job and "Bash(git switch" not in job


def test_preview_link_only_goes_to_claude_issue_branches():
    wf = read(".github/workflows/issue-preview-link.yml")
    assert "^claude/issue-([0-9]+)-" in wf
    assert "state == 'success'" in wf
    assert "${{ github.event" not in wf.split("run: |", 1)[1], "event values must reach the script through env, not inline"


def test_signin_check_only_runs_by_hand_and_never_touches_the_repo():
    wf = read(".github/workflows/check-claude-signin.yml")
    assert "\non: workflow_dispatch\n" in wf, "only people with write access should be able to start it"
    assert "contents: write" not in wf and "actions/checkout" not in wf
    assert "${{ github.event" not in wf and "${{ steps" not in wf.split("run: |", 1)[1], "no event text inside scripts"
