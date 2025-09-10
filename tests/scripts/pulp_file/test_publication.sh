#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "file" || exit 23

cleanup() {
  pulp file repository destroy --name "cli_test_file_publication_repository" || true
  pulp file remote destroy --name "cli_test_file_publication_remote" || true
}
trap cleanup EXIT

pulp file remote create --name "cli_test_file_publication_remote" --url "$FILE_REMOTE_URL"
pulp file repository create --name "cli_test_file_publication_repository" --remote "cli_test_file_publication_remote"
pulp file repository sync --name "cli_test_file_publication_repository"

expect_succ pulp file publication create --repository "cli_test_file_publication_repository"

PUBLICATION_HREF="$(echo "$OUTPUT" | jq -r .pulp_href)"
expect_succ pulp file publication destroy --href "$PUBLICATION_HREF"
expect_succ pulp file publication create --repository "cli_test_file_publication_repository" --version 0
PUBLICATION_HREF="$(echo "$OUTPUT" | jq -r .pulp_href)"
if pulp debug has-plugin --name "core" --specifier ">=3.20.0"
then
  expect_succ pulp file publication list --repository "cli_test_file_publication_repository"
  test "$(echo "$OUTPUT" | jq -r length)" -eq 1
  expect_succ pulp publication list --repository "file:file:cli_test_file_publication_repository"
  test "$(echo "$OUTPUT" | jq -r length)" -eq 1
fi
expect_succ pulp file publication destroy --href "$PUBLICATION_HREF"
