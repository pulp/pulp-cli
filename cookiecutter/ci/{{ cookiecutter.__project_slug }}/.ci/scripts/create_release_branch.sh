#!/bin/bash

set -eu -o pipefail

BRANCH="$(git branch --show-current)"

if ! [[ "${BRANCH}" = "main" ]]
then
  echo ERROR: This is not the main branch!
  exit 1
fi

NEW_BRANCH="$(bump2version --dry-run --list release | sed -Ene 's/^new_version=([[:digit:]]+\.[[:digit:]]+)\..*$/\1/p')"

if [[ -z "${NEW_BRANCH}" ]]
then
  echo ERROR: Could not parse new version.
  exit 1
fi

git branch "${NEW_BRANCH}"

# Clean changelog snippets.
find CHANGES/ \( -name "*.feature" -o -name "*.bugfix" -o -name "*.doc" -o -name "*.translation" -o -name "*.devel" -o -name "*.misc" \) -exec git rm -f \{\} +
{%- if cookiecutter.docs %}

# Add to version.txt
sed -i -e "1 i \\${NEW_BRANCH}" docs/versions.txt
git add docs/versions.txt
{%- endif %}

bump2version minor --commit --message $'Bump version to {new_version}\n\n[noissue]' --allow-dirty

git push origin "${NEW_BRANCH}"
