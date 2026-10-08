#!/usr/bin/env bash
# Optional shortcut for GitHub CLI users. Run in the unzipped directory.
set -euo pipefail
gh auth status >/dev/null || gh auth login
git init
git add .
git commit -m 'Initial CFB Intelligence app'
git branch -M main
gh repo create cfb-intelligence --private --source=. --remote=origin --push
printf '\nRepository created. Run the Refresh college football data workflow from GitHub Actions.\n'
