#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "core" --min-version "3.15.1" || exit 23

cleanup() {
  pulp content-guard rbac destroy --name "cli_test_guard" || true
  pulp group destroy --name "cli_test_group" || true
}
trap cleanup EXIT

expect_succ pulp content-guard rbac create --name "cli_test_guard"
expect_succ pulp content-guard list
test "$(echo "$OUTPUT" | jq -r length)" -gt "0"
expect_succ pulp content-guard rbac list --name "cli_test_guard"
test "$(echo "$OUTPUT" | jq -r length)" -eq "1"
expect_succ pulp content-guard rbac show --name "cli_test_guard"

expect_succ pulp group create --name "cli_test_group"
expect_succ pulp content-guard rbac assign --name "cli_test_guard" --group "cli_test_group"
expect_succ pulp content-guard rbac show --name "cli_test_guard"
test "$(echo "$OUTPUT" | jq -r '.groups' | jq -r length)" -eq "1"
expect_succ pulp content-guard rbac remove --name "cli_test_guard" --user "admin" --group "cli_test_group"
expect_succ pulp content-guard rbac show --name "cli_test_guard"
test "$(echo "$OUTPUT" | jq -r '.users' | jq -r length)" -eq "0"
test "$(echo "$OUTPUT" | jq -r '.groups' | jq -r length)" -eq "0"

expect_succ pulp content-guard rbac destroy --name "cli_test_guard"
