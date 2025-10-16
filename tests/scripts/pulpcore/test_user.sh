#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

cleanup() {
  pulp user destroy --username "core-user-clitest" || true
}
trap cleanup EXIT

expect_succ pulp user list
expect_succ pulp user show --username admin
expect_succ pulp user create --username "core-user-clitest" --password "Yeech6ba"
expect_succ pulp user update --username "core-user-clitest" --first-name "cli" --last-name "test"
