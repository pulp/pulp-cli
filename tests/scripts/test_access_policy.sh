#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")/config.source"

SAVED_ACCESS_POLICY="$(pulp access-policy show --viewset-name "tasks")"

cleanup() {
  pulp access-policy update --viewset-name "tasks" --statements "$(echo "$SAVED_ACCESS_POLICY" | jq '.statements')" --permissions-assignment "$(echo "$SAVED_ACCESS_POLICY" | jq '.permissions_assignment')" || true
}
trap cleanup EXIT

cleanup

# Prepare
expect_succ pulp access-policy list
expect_succ pulp access-policy show --viewset-name "tasks"
expect_succ pulp access-policy update --viewset-name "tasks" --statements "$(echo "$SAVED_ACCESS_POLICY" | jq '.statements')" --permissions-assignment "$(echo "$SAVED_ACCESS_POLICY" | jq '.permissions_assignment')"
