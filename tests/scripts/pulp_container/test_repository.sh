#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "pulp_container" || exit 3

cleanup() {
  pulp container repository destroy --name "cli_test_container_repo" || true
}
trap cleanup EXIT

expect_succ pulp container repository list

expect_succ pulp container repository create --name "cli_test_container_repo" --description "Test repository for CLI tests"
expect_succ pulp container repository update --name "cli_test_container_repo" --description ""
expect_succ pulp container repository show --name "cli_test_container_repo"
test "$(echo "$OUTPUT" | jq -r '.description')" = "null"
expect_succ pulp container repository list
expect_succ pulp container repository destroy --name "cli_test_container_repo"
