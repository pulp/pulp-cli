#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")/config.source"

cleanup() {
  pulp file repository --name "cli_test_file_repo" destroy || true
}
trap cleanup EXIT

expect_succ pulp file repository list

expect_succ pulp file repository create --name "cli_test_file_repo"
expect_succ pulp file repository --name "cli_test_file_repo" update --description "Test repository for CLI tests"
expect_succ pulp file repository list
expect_succ pulp file repository --name "cli_test_file_repo" destroy
