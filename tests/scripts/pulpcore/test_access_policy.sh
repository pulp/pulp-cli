#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

SAVED_ACCESS_POLICY="$(pulp access-policy show --viewset-name "tasks")"
SAVED_STATEMENTS="$(echo "$SAVED_ACCESS_POLICY" | jq '.statements')"
SAVED_CREATION_HOOKS="$(echo "$SAVED_ACCESS_POLICY" | jq '.creation_hooks // .permissions_assignment')"

cleanup() {
    pulp access-policy reset --viewset-name tasks || true
}
trap cleanup EXIT

cleanup

# Prepare
expect_succ pulp access-policy list
expect_succ pulp access-policy show --viewset-name "tasks"
expect_succ pulp access-policy update --viewset-name "tasks" --statements "$SAVED_STATEMENTS"
expect_succ pulp access-policy update --viewset-name "tasks" --creation-hooks "$SAVED_CREATION_HOOKS"
expect_succ pulp access-policy update --viewset-name "tasks" --statements "$SAVED_STATEMENTS" --creation-hooks "$SAVED_CREATION_HOOKS"

expect_succ pulp access-policy reset --viewset-name tasks
