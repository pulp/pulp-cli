#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "file" --min-version "1.9.0.dev" || exit 3

acs_remote="cli_test_file_acs_remote"
acs="cli_test_acs"

cleanup() {
  pulp file acs destroy --name $acs || true
  pulp file remote destroy --name $acs_remote || true
}
trap cleanup EXIT

cleanup

expect_succ pulp file remote create --name $acs_remote --url "http://example.com" --policy "on_demand"

expect_succ pulp file acs create --name $acs --remote $acs_remote --path "ab/" --path "cd/"
expect_succ pulp file acs list
test "$(echo "$OUTPUT" | jq -r length)" -ge 1
expect_succ pulp file acs show --name $acs
test "$(echo "$OUTPUT" | jq ".paths | length")" -eq 2

expect_succ pulp file acs path add --name $acs --path "ok/" --path "no/"
expect_succ pulp file acs show --name $acs
test "$(echo "$OUTPUT" | jq ".paths | length")" -eq 4

expect_succ pulp file acs path remove --name $acs --path "ab/"
expect_succ pulp file acs show --name $acs
test "$(echo "$OUTPUT" | jq ".paths | length")" -eq 3

expect_succ pulp file acs destroy --name $acs
