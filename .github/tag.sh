#!/usr/bin/env bash
set -ex

git fetch --tags
EXISTING_TAGS=$(git tag --list)
VERSION=$(sed -E -n 's/^__version__ = "([0-9]+\.[0-9]+\.[0-9]+)"$/\1/p' src/esok/__init__.py)

if [[ ! $EXISTING_TAGS =~ $VERSION ]]; then
  echo "New version detected. Pushing new tag!"

  git config --local user.email "action@github.com"
  git config --local user.name "GitHub Action"

  git tag "$VERSION"
  git push --tags
else
  echo "$VERSION already published. No action taken."
fi
