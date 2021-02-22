#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "container" || exit 3

cleanup() {
  pulp container remote destroy --name "cli_test_container_remote" || true
}
trap cleanup EXIT

cleanup

expect_succ pulp container remote list

expect_succ pulp container remote create --name "cli_test_container_remote" --upstream-name "hello" --url "$FILE_REMOTE_URL"
expect_succ pulp container remote list
expect_succ pulp container remote destroy --name "cli_test_container_remote"
