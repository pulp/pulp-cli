#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

cleanup() {
  pulp group destroy --name "cli_test_group" || true
}
trap cleanup EXIT

expect_succ pulp group list
expect_succ pulp group create --name "cli_test_group"
expect_succ pulp group show --name "cli_test_group"
expect_succ pulp group list

expect_succ pulp group user add --groupname "cli_test_group" --username "admin"
expect_succ pulp group user add --groupname "cli_test_group" --username "AnonymousUser"
expect_succ pulp group user list --groupname "cli_test_group"
expect_succ pulp group user remove --groupname "cli_test_group" --username "admin"

expect_succ pulp group destroy --name "cli_test_group"
