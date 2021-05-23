#!/usr/bin/env bash
set -ex

VERSION=$(sed -E -n 's/^__version__ = "([0-9]+\.[0-9]+\.[0-9]+)"$/\1/p' src/esok/__init__.py)
EXISTING_TAGS=$(git tag --list)

if [[ ! $EXISTING_TAGS =~ $VERSION ]]; then
  echo "New version detected. Pushing new tag!"

  git config --local user.email "action@github.com"
  git config --local user.name "GitHub Action"

  git tag "$VERSION"
  git push --tags
else
  echo "$VERSION already published. No action taken."
fi
