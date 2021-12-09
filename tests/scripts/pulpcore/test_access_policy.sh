#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

SAVED_ACCESS_POLICY="$(pulp access-policy show --viewset-name "tasks")"
SAVED_STATEMENTS="$(echo "$SAVED_ACCESS_POLICY" | jq '.statements')"
SAVED_CREATION_HOOKS="$(echo "$SAVED_ACCESS_POLICY" | jq '.creation_hooks // .permissions_assignment')"

cleanup() {
  if pulp debug has-plugin --name "core" --min-version "3.17.0.dev"
  then
    pulp access-policy reset --viewset-name tasks || true
  else
    pulp access-policy update --viewset-name "tasks" --statements "$SAVED_STATEMENTS" --creation-hooks "$SAVED_CREATION_HOOKS" || true
  fi
}
trap cleanup EXIT

cleanup

# Prepare
expect_succ pulp access-policy list
expect_succ pulp access-policy show --viewset-name "tasks"
expect_succ pulp access-policy update --viewset-name "tasks" --statements "$SAVED_STATEMENTS" --creation-hooks "$SAVED_CREATION_HOOKS"

if pulp debug has-plugin --name "core" --min-version "3.17.0.dev"
then
  expect_succ pulp access-policy reset --viewset-name tasks
fi
