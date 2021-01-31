#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "pulpcore" --min-version "3.10.0" || exit 3

cleanup() {
  pulp file repository destroy --name "cli_test_file_repo" || true
}
trap cleanup EXIT

name="cli_test_file_repo"
expect_succ pulp file repository create --name "$name"
expect_succ pulp file repository label set --name "$name" --key "atani" --value "hurin"
expect_succ pulp file repository label set --name "$name" --key "ainur" --value "ulmo"

expect_succ pulp file repository show --name "$name"
test "$(echo "$OUTPUT" | jq -Src .pulp_labels)" = '{"ainur":"ulmo","atani":"hurin"}'

# update a label
expect_succ pulp file repository label set --name "$name" --key "atani" --value "beor"
expect_succ pulp file repository show --name "$name"
test "$(echo "$OUTPUT" | jq -Src .pulp_labels)" = '{"ainur":"ulmo","atani":"beor"}'
expect_succ pulp file repository label show --name "$name" --key "atani"
test "$OUTPUT" = "beor"

# remove a label
expect_succ pulp file repository label unset --name "$name" --key "atani"
expect_succ pulp file repository show --name "$name"
test "$(echo "$OUTPUT" | jq -Src .pulp_labels)" = '{"ainur":"ulmo"}'
expect_fail pulp file repository label show --name "$name"

# filtering
expect_succ pulp file repository label set --name "$name" --key "istar" --value "olorin"
expect_succ pulp file repository list --label-select "ainur"
test "$(echo "$OUTPUT" | jq length)" -eq 1
expect_succ pulp file repository list --label-select "ainur=ulmo"
test "$(echo "$OUTPUT" | jq length)" -eq 1
expect_succ pulp file repository list --label-select "ainur~lm"
test "$(echo "$OUTPUT" | jq length)" -eq 1
expect_succ pulp file repository list --label-select 'ainur=ulmo,istar!=curumo'
test "$(echo "$OUTPUT" | jq length)" -eq 1
expect_succ pulp file repository list --label-select "ainur=ulmo,istar=olorin"
test "$(echo "$OUTPUT" | jq length)" -eq 1
expect_succ pulp file repository list --label-select 'ainur=ulmo,!istar'
test "$(echo "$OUTPUT" | jq length)" -eq 0
