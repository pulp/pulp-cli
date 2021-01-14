#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")/config.source"

cleanup() {
  pulp ansible repository destroy --name "cli_test_ansible_repo" || true
}
trap cleanup EXIT

expect_succ pulp ansible repository list

expect_succ pulp ansible repository create --name "cli_test_ansible_repo"
expect_succ pulp ansible repository update --name "cli_test_ansible_repo" --description "Test repository for CLI tests"
expect_succ pulp ansible repository list
expect_succ pulp ansible repository destroy --name "cli_test_ansible_repo"
