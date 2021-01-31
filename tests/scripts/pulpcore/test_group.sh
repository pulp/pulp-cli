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
expect_succ pulp group user --groupname "cli_test_group" add --username "admin"
expect_succ pulp group user --groupname "cli_test_group" add --username "AnonymousUser"
expect_succ pulp group user --groupname "cli_test_group" remove --username "admin"
expect_succ pulp group destroy --name "cli_test_group"
