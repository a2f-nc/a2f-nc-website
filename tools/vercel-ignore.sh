#!/usr/bin/env bash
# Vercel runs this before building (see "ignoreCommand" in vercel.json).
#   exit 0 = skip this build (only behind-the-scenes files changed)
#   exit 1 = build and publish as usual
# Anything unexpected exits 1, so the worst case is an extra deploy, never a missing one.
# The "behind the scenes" list matches .vercelignore: files that are not part of the website.

# Vercel gives us the last commit it handled on this branch. With no answer, just build.
base="${VERCEL_GIT_PREVIOUS_SHA:-}"
[ -n "$base" ] || { echo "No previous commit known: building."; exit 1; }
git cat-file -e "$base^{commit}" 2>/dev/null || { echo "Previous commit not available: building."; exit 1; }

changed=$(git diff --name-only "$base" HEAD) || { echo "Could not compare commits: building."; exit 1; }
[ -n "$changed" ] || { echo "No changed files found: building."; exit 1; }

while IFS= read -r file; do
  case "$file" in
    .github/*|tests/*|tools/*|README.md|CLAUDE.md|SETUP.md|requirements-dev.txt|pytest.ini|.gitignore|.vercelignore) ;;
    *) echo "Website file changed ($file): building."; exit 1 ;;
  esac
done <<< "$changed"

echo "Only behind-the-scenes files changed: skipping this build."
exit 0
