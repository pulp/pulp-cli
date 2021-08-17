#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "python" --min-version "3.1.0.dev" || exit 3

cleanup() {
  rm "shelf-reader-0.1.tar.gz"
  pulp python repository destroy --name "cli_test_python_repository" || true
  pulp orphans delete || true
}
trap cleanup EXIT

# Test python upload
wget "https://fixtures.pulpproject.org/python-pypi/packages/shelf-reader-0.1.tar.gz"
sha256=$(sha256sum "shelf-reader-0.1.tar.gz" | cut -d' ' -f1)

expect_succ pulp python content upload --file "shelf-reader-0.1.tar.gz" --relative-path "shelf-reader-0.1.tar.gz"
expect_succ pulp artifact list --sha256 "$sha256"
expect_succ pulp python content list --filename "shelf-reader-0.1.tar.gz"
content_href="$(echo "$OUTPUT" | tr '\r\n' ' ' | jq -r .[0].pulp_href)"
expect_succ pulp python content show --href "$content_href"

expect_succ pulp python repository create --name "cli_test_python_repository"
expect_succ pulp python repository add --name "cli_test_python_repository" --filename "shelf-reader-0.1.tar.gz"
expect_succ pulp python repository add --name "cli_test_python_repository" --filename "shelf-reader-0.1.tar.gz" --base-version 0
expect_succ pulp python repository remove --name "cli_test_python_repository" --filename "shelf-reader-0.1.tar.gz"
expect_succ pulp python repository remove --name "cli_test_python_repository" --filename "shelf-reader-0.1.tar.gz" --base-version 1
