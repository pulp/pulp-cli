#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "container" || exit 23

cleanup() {
  pulp container namespace destroy --name "cli_test_container_namespace" || true
}
trap cleanup EXIT

cleanup

expect_succ pulp container namespace list

expect_succ pulp container namespace create --name "cli_test_container_namespace"
expect_succ pulp container namespace list
expect_succ pulp container namespace destroy --namespace "cli_test_container_namespace"
