#!/bin/bash

set -eu -o pipefail

BRANCH="$(git branch --show-current)"

if ! [[ "${BRANCH}" = "main" ]]
then
  echo ERROR: This is not the main branch!
  exit 1
fi

NEW_BRANCH="$(bump-my-version show new_version --increment release | sed -Ene 's/^([[:digit:]]+\.[[:digit:]]+)\.[[:digit:]]+$/\1/p')"

if [[ -z "${NEW_BRANCH}" ]]
then
  echo ERROR: Could not parse new version.
  exit 1
fi

git branch "${NEW_BRANCH}"

# Clean changelog snippets.
find CHANGES/ \( -name "*.feature" -o -name "*.bugfix" -o -name "*.removal" -o -name "*.doc" -o -name "*.translation" -o -name "*.devel" -o -name "*.misc" \) -exec git rm -f \{\} +

bump-my-version bump minor --commit --message $'Bump version to {new_version}' --allow-dirty

git push origin "${NEW_BRANCH}"

if [ "${GITHUB_ENV:-}" ]
then
  echo "NEW_BRANCH=${NEW_BRANCH}" >> "${GITHUB_ENV}"
fi
