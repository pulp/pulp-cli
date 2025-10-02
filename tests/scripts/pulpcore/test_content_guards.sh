#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

cleanup() {
  pulp content-guard composite destroy --name "cli_test_composite_guard" || true
  pulp content-guard header destroy --name "cli_test_header_guard" || true
  pulp content-guard rbac destroy --name "cli_test_rbac_guard" || true
  pulp group destroy --name "cli_test_content_guard_group" || true
}
trap cleanup EXIT

expect_succ pulp content-guard rbac create --name "cli_test_rbac_guard"
expect_succ pulp content-guard list
test "$(echo "$OUTPUT" | jq -r length)" -gt "0"
expect_succ pulp content-guard rbac list --name "cli_test_rbac_guard"
test "$(echo "$OUTPUT" | jq -r length)" -eq "1"
expect_succ pulp content-guard rbac show --name "cli_test_rbac_guard"

expect_succ pulp group create --name "cli_test_content_guard_group"
expect_succ pulp content-guard rbac assign --name "cli_test_rbac_guard" --group "cli_test_content_guard_group"
expect_succ pulp content-guard rbac show --name "cli_test_rbac_guard"
test "$(echo "$OUTPUT" | jq -r '.groups' | jq -r length)" -eq "1"
expect_succ pulp content-guard rbac remove --name "cli_test_rbac_guard" --user "admin" --group "cli_test_content_guard_group"
expect_succ pulp content-guard rbac show --name "cli_test_rbac_guard"
test "$(echo "$OUTPUT" | jq -r '.users' | jq -r length)" -eq "0"
test "$(echo "$OUTPUT" | jq -r '.groups' | jq -r length)" -eq "0"

if pulp debug has-plugin --name "core" --specifier ">=3.39.0"
then
  # Header content guard
  expect_succ pulp content-guard header create --name "cli_test_header_guard" --header-name "to" --header-value "ken"
  if pulp debug has-plugin --name "core" --specifier ">=3.43.0"
  then
    # Composite content guard
    expect_succ pulp content-guard composite create --name "cli_test_composite_guard" --guard "rbac:cli_test_rbac_guard" --guard "header:cli_test_header_guard"
    test "$(echo "$OUTPUT" | jq -r '.guards' | jq -r length)" -eq "2"
    expect_succ pulp content-guard composite update --name "cli_test_composite_guard" --guard "rbac:cli_test_rbac_guard" --description "Updated composite guard"
    expect_succ pulp content-guard composite show --name "cli_test_composite_guard"
    test "$(echo "$OUTPUT" | jq -r '.guards' | jq -r length)" -eq "1"
    expect_succ pulp content-guard composite destroy --name "cli_test_composite_guard"
  fi
  expect_succ pulp content-guard header destroy --name "cli_test_header_guard"
fi

expect_succ pulp content-guard rbac destroy --name "cli_test_rbac_guard"
