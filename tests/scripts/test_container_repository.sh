#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")/config.source"

cleanup() {
  pulp container repository destroy --name "cli_test_container_repo" || true
}
trap cleanup EXIT

expect_succ pulp container repository list

expect_succ pulp container repository create --name "cli_test_container_repo"
expect_succ pulp container repository update --name "cli_test_container_repo" --description "Test repository for CLI tests"
expect_succ pulp container repository list
expect_succ pulp container repository destroy --name "cli_test_container_repo"
