#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "file" || exit 23

cleanup() {
  pulp file repository destroy --name "cli_test_file_distribution_repository" || true
  pulp file remote destroy --name "cli_test_file_distribution_remote" || true
  pulp file distribution destroy --name "cli_test_file_distro" || true
  pulp content-guard rbac destroy --name "cli_test_file_content_guard" || true
}
trap cleanup EXIT

expect_succ pulp file remote create --name "cli_test_file_distribution_remote" --url "$FILE_REMOTE_URL"
expect_succ pulp file repository create --name "cli_test_file_distribution_repository" --remote "cli_test_file_distribution_remote"
expect_succ pulp file repository sync --repository "cli_test_file_distribution_repository"
expect_succ pulp file publication create --repository "cli_test_file_distribution_repository"
PUBLICATION_HREF=$(echo "$OUTPUT" | jq -r .pulp_href)
expect_succ pulp content-guard rbac create --name "cli_test_file_content_guard"
CONTENT_GUARD_HREF=$(echo "$OUTPUT" | jq -r .pulp_href)

expect_succ pulp file distribution create \
  --name "cli_test_file_distro" \
  --base-path "file_wrong_path" \
  --publication "$PUBLICATION_HREF" \
  --content-guard "core:rbac:cli_test_file_content_guard"
expect_succ pulp file distribution update \
  --name "cli_test_file_distro" \
  --publication "" \
  --content-guard "$CONTENT_GUARD_HREF"
# Empty content guard needs to go last, because we want to download later...
expect_succ pulp file distribution update \
  --name "cli_test_file_distro" \
  --base-path "cli_test_file_distro" \
  --publication "$PUBLICATION_HREF" \
  --content-guard ""

if pulp debug has-plugin --name "file" --specifier ">=1.7.0"
then
  expect_succ pulp file distribution update \
    --distribution "cli_test_file_distro" \
    --repository "cli_test_file_distribution_repository"
fi

expect_succ pulp file distribution list --base-path "cli_test_file_distro"
test "$(echo "$OUTPUT" | jq -r length)" -eq 1

expect_succ pulp file distribution list --base-path-contains "CLI"
test "$(echo "$OUTPUT" | jq -r length)" -gt 0

expect_succ pulp file distribution destroy --distribution "cli_test_file_distro"
