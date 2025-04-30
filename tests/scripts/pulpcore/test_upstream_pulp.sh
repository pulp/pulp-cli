#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "core" --specifier ">=3.23.0" || exit 23

cleanup() {
  pulp upstream-pulp destroy --upstream-pulp "cli_test_upstream_pulp" || true
}
trap cleanup EXIT

expect_succ pulp upstream-pulp create --name "cli_test_upstream_pulp" --base-url "$PULP_BASE_URL" --api-root "/123/"
expect_succ pulp upstream-pulp show --upstream-pulp "cli_test_upstream_pulp"
expect_succ pulp upstream-pulp list

if pulp debug has-plugin --name "core" --specifier "<=3.62.0"
then
  expect_succ pulp upstream-pulp update --id "cli_test_upstream_pulp" --pulp-label-select "doesnotexist"
else
  expect_succ pulp upstream-pulp update --id "cli_test_upstream_pulp" --q-select "pulp_label_select=doesnotexist"
fi

if pulp debug has-plugin --name "core" --specifier ">=3.73.0"
then
  expect_succ pulp upstream-pulp update --id "cli_test_upstream_pulp" --policy "nodelete"
  expect_succ pulp upstream-pulp update --id "cli_test_upstream_pulp" --policy "labeled"
  expect_fail pulp upstream-pulp update --id "cli_test_upstream_pulp" --policy "not_a_policy"
fi

# Without credentials and a wrong API root, there is not much we can do...
# Also this is a real dangerous command, deleting all existing repositories.
expect_fail pulp upstream-pulp replicate --id "cli_test_upstream_pulp"

expect_succ pulp upstream-pulp destroy --id "cli_test_upstream_pulp"
