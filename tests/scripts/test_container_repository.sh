#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")/config.source"

cleanup() {
  pulp container repository --name "cli_test_container_repo" destroy || true
  pulp container repository --type push --name "cli_test_container_push_repo" destroy || true
}
trap cleanup EXIT

expect_succ pulp container repository list

expect_succ pulp container repository create --name "cli_test_container_repo"
expect_succ pulp container repository --name "cli_test_container_repo" show
expect_succ pulp container repository --name "cli_test_container_repo" update --description "Test repository for CLI tests"
expect_succ pulp container repository list
expect_succ pulp container repository --name "cli_test_container_repo" destroy

# Skip push repository tests due to https://pulp.plan.io/issues/7839
# expect_succ pulp container repository --type push list

# expect_succ pulp container repository --type push create --name "cli_test_container_push_repo"
# expect_succ pulp container repository --type push show --name "cli_test_container_push_repo"
# expect_fail pulp container repository --type push update --name "cli_test_container_push_repo" --description "Test repository for CLI tests"
# expect_succ pulp container repository --type push list
# expect_succ pulp container repository --type push destroy --name "cli_test_container_push_repo"
