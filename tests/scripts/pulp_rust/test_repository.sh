#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "rust" || exit 23

cleanup() {
  pulp rust repository destroy --name "cli_test_rust_repo" || true
  pulp rust remote destroy --name "cli_test_rust_repo_remote" || true
}
trap cleanup EXIT

REMOTE_HREF="$(pulp rust remote create --name "cli_test_rust_repo_remote" --url "sparse+https://index.crates.io/" | jq -r '.pulp_href')"

expect_succ pulp rust repository list

expect_succ pulp rust repository create --name "cli_test_rust_repo" --description "Test repository for CLI tests"
HREF="$(echo "$OUTPUT" | jq -r '.pulp_href')"

expect_succ pulp rust repository update --repository "cli_test_rust_repo" --remote "cli_test_rust_repo_remote"
expect_succ pulp rust repository show --repository "cli_test_rust_repo"
test "$(echo "$OUTPUT" | jq -r '.remote')" = "$REMOTE_HREF"

expect_succ pulp rust repository update --repository "cli_test_rust_repo" --description ""
expect_succ pulp rust repository show --repository "$HREF"
test "$(echo "$OUTPUT" | jq -r '.description')" = "null"

expect_succ pulp rust repository update --repository "cli_test_rust_repo" --remote ""
expect_succ pulp rust repository show --repository "cli_test_rust_repo"
test "$(echo "$OUTPUT" | jq -r '.remote')" = "null"

expect_succ pulp rust repository list
test "$(echo "$OUTPUT" | jq -r '.|length')" != "0"

expect_succ pulp rust repository task list --repository "cli_test_rust_repo"

expect_succ pulp rust repository destroy --repository "cli_test_rust_repo"
