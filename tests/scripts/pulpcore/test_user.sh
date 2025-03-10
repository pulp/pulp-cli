#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

cleanup() {
  pulp user destroy --username "clitest" || true
}
trap cleanup EXIT

expect_succ pulp user list
expect_succ pulp user show --username admin
expect_succ pulp user create --username "clitest" --password "Yeech6ba"
expect_succ pulp user update --username "clitest" --first-name "cli" --last-name "test"
