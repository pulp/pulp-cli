#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "container" || exit 3

cleanup() {
  pulp container repository destroy --name "cli_test_container_repo" || true
}
trap cleanup EXIT

expect_succ pulp container repository list

expect_succ pulp container repository create --name "cli_test_container_repo" --description "Test repository for CLI tests"
expect_succ pulp container repository update --repository "cli_test_container_repo" --description ""
expect_succ pulp container repository show --repository "cli_test_container_repo"
test "$(echo "$OUTPUT" | jq -r '.description')" = "null"
expect_succ pulp container repository list
expect_succ pulp container repository destroy --repository "cli_test_container_repo"

expect_succ pulp container repository -t "push" --help
test "$(echo "$OUTPUT" | grep -E "create|update|destroy|sync")" = ""
