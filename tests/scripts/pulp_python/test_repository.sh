#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "python" || exit 23

cleanup() {
  pulp python repository destroy --name "cli_test_python_repo" || true
  pulp python remote destroy --name "cli_test_python_repository_remote1" || true
  pulp python remote destroy --name "cli_test_python_repository_remote2" || true
}
trap cleanup EXIT

REMOTE1_HREF="$(pulp python remote create --name "cli_test_python_repository_remote1" --url "http://a/" | jq -r '.pulp_href')"
REMOTE2_HREF="$(pulp python remote create --name "cli_test_python_repository_remote2" --url "http://b/" | jq -r '.pulp_href')"

expect_succ pulp python repository list

expect_succ pulp python repository create --name "cli_test_python_repo" --description "Test repository for CLI tests"
expect_succ pulp python repository update --repository "cli_test_python_repo" --description "" --remote "cli_test_python_repository_remote1"
expect_succ pulp python repository show --repository "cli_test_python_repo"
expect_succ test "$(echo "$OUTPUT" | jq -r '.remote')" = "$REMOTE1_HREF"
expect_succ pulp python repository update --repository "cli_test_python_repo" --remote "cli_test_python_repository_remote2"
expect_succ pulp python repository show --repository "cli_test_python_repo"
expect_succ test "$(echo "$OUTPUT" | jq -r '.remote')" = "$REMOTE2_HREF"
expect_succ pulp python repository update --repository "cli_test_python_repo" --remote ""
expect_succ pulp python repository show --repository "cli_test_python_repo"
expect_succ test "$(echo "$OUTPUT" | jq -r '.description')" = "null"
expect_succ test "$(echo "$OUTPUT" | jq -r '.remote')" = ""
expect_succ pulp python repository list
test "$(echo "$OUTPUT" | jq -r '.|length')" != "0"

expect_succ pulp python repository destroy --name "cli_test_python_repo"
