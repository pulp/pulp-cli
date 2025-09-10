#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "file" --specifier ">=1.6.0" || exit 23

cleanup() {
  pulp file repository destroy --name "cli_test_file_label_repo" || true
}
trap cleanup EXIT

name="cli_test_file_label_repo"
expect_succ pulp file repository create --name "$name" --labels '{"atani": "hurin"}'
expect_succ pulp file repository label set --repository "$name" --key "ainur" --value "ulmo"

expect_succ pulp file repository show --repository "$name"
test "$(echo "$OUTPUT" | jq -Src .pulp_labels)" = '{"ainur":"ulmo","atani":"hurin"}'

# update a label
expect_succ pulp file repository label set --repository "$name" --key "atani" --value "beor"
expect_succ pulp file repository show --repository "$name"
test "$(echo "$OUTPUT" | jq -Src .pulp_labels)" = '{"ainur":"ulmo","atani":"beor"}'
expect_succ pulp file repository label show --repository "$name" --key "atani"
test "$OUTPUT" = "beor"

# remove a label
expect_succ pulp file repository label unset --repository "$name" --key "atani"
expect_succ pulp file repository show --repository "$name"
test "$(echo "$OUTPUT" | jq -Src .pulp_labels)" = '{"ainur":"ulmo"}'
expect_fail pulp file repository label show --repository "$name"

# filtering
expect_succ pulp file repository label set --repository "$name" --key "istar" --value "olorin"
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

# Test content label
if pulp debug has-plugin --name "core" --specifier ">=3.73.2"
then
  echo "hi" > hi.txt
  expect_succ pulp file content upload --file hi.txt --relative-path hi.txt --repository "$name"
  expect_succ pulp file content list --sha256 "$(sha256sum hi.txt | cut -d' ' -f1)"
  test "$(echo "$OUTPUT" | jq -r length)" -eq 1
  content_href="$(echo "$OUTPUT" | jq -r .[0].pulp_href)"
  expect_succ pulp file content label set --href "$content_href" --key "test" --value "value"
  expect_succ pulp file content label show --href "$content_href" --key "test"
  test "$OUTPUT" = "value"
  expect_succ pulp file content list --label-select "test"
  test "$(echo "$OUTPUT" | jq length)" -eq 1
  expect_succ pulp file content label unset --href "$content_href" --key "test"
  expect_fail pulp file content label show --href "$content_href" --key "test"
fi