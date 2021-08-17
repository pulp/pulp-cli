#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "file" || exit 3

cleanup() {
  pulp file remote destroy --name "cli_test_file_remote" || true
  pulp file repository destroy --name "cli_test_file_repository" || true
  pulp file distribution destroy --name "cli_test_file_distro" || true
}
trap cleanup EXIT

if [ "$VERIFY_SSL" = "false" ]
then
  curl_opt="-k"
else
  curl_opt=""
fi

expect_succ pulp file remote create --name "cli_test_file_remote" --url "$FILE_REMOTE_URL"
expect_succ pulp file repository create --name "cli_test_file_repository" --remote "cli_test_file_remote"
expect_succ pulp file repository sync --name "cli_test_file_repository"
expect_succ pulp file publication create --repository "cli_test_file_repository"
PUBLICATION_HREF=$(echo "$OUTPUT" | jq -r .pulp_href)

expect_succ pulp file distribution create \
  --name "cli_test_file_distro" \
  --base-path "wrong_path" \
  --publication "$PUBLICATION_HREF"
expect_succ pulp file distribution update \
  --name "cli_test_file_distro" \
  --publication ""
expect_succ pulp file distribution update \
  --name "cli_test_file_distro" \
  --base-path "cli_test_file_distro" \
  --publication "$PUBLICATION_HREF"

if [ "$(pulp debug has-plugin --name "file" --min-version "1.7.0.dev")" = "true" ]
then
  expect_succ pulp file distribution update \
    --name "cli_test_file_distro" \
    --repository "cli_test_file_repository"
fi

expect_succ pulp file distribution list --base-path "cli_test_file_distro"
test "$(echo "$OUTPUT" | jq -r length)" -eq 1
expect_succ pulp file distribution list --base-path-contains "CLI"
test "$(echo "$OUTPUT" | jq -r length)" -gt 0

expect_succ curl "$curl_opt" --head --fail "$PULP_BASE_URL/pulp/content/cli_test_file_distro/1.iso"

expect_succ pulp file distribution destroy --name "cli_test_file_distro"
