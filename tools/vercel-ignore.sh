#!/usr/bin/env bash
# Vercel runs this before building (see "ignoreCommand" in vercel.json).
#   exit 0 = skip this build (only behind-the-scenes files changed)
#   exit 1 = build and publish as usual
# Anything unexpected exits 1, so the worst case is an extra deploy, never a missing one.
# The "behind the scenes" list matches .vercelignore: files that are not part of the website.

# Compare against the last commit Vercel handled on this branch when it tells us (VERCEL_GIT_PREVIOUS_SHA).
# Vercel often leaves that empty, so the fallback is the commit just before this one. That is exact for the
# usual one-commit push. For the live site (the main branch) we don't guess: with no answer, build.
base="${VERCEL_GIT_PREVIOUS_SHA:-}"
if [ -n "$base" ]; then
  git cat-file -e "$base^{commit}" 2>/dev/null || { echo "Previous commit not available: building."; exit 1; }
else
  if [ "${VERCEL_GIT_COMMIT_REF:-}" = "main" ] || [ "${VERCEL_ENV:-}" = "production" ]; then
    echo "No previous commit known for the live site: building."; exit 1
  fi
  base="HEAD^"
  git cat-file -e "$base^{commit}" 2>/dev/null || { echo "No earlier commit to compare: building."; exit 1; }
fi

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
