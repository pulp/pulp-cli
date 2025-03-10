#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "file" || exit 23

eval "$(pulp status | jq -r '.domain_enabled // false | not')" || exit 23

cleanup() {
  pulp importer pulp destroy --name "cli_test_importer" || true
  pulp file repository destroy --name dest1 || true
  pulp file repository destroy --name dest2 || true
}
trap cleanup EXIT

expect_succ pulp file repository create --name dest1
expect_succ pulp file repository create --name dest2

# create, show, destroy
expect_succ pulp importer pulp create --name "cli_test_importer"
expect_succ pulp importer pulp show --name "cli_test_importer"
expect_succ pulp importer pulp list --name "cli_test_importer"
test "$(echo "$OUTPUT" | jq -r length)" -eq 1
expect_succ pulp importer pulp destroy --name "cli_test_importer"

# create with a repo mapping
expect_succ pulp importer pulp create --name "cli_test_importer" --repo-map src1 dest1
test "$(echo "$OUTPUT" | jq '.repo_mapping' | jq -r length)" -eq 1
test "$(echo "$OUTPUT" | jq '.repo_mapping.src1')" = "\"dest1\""

# update repo mapping
expect_succ pulp importer pulp update --name "cli_test_importer" --repo-map src1 dest1 --repo-map src2 dest2
test "$(echo "$OUTPUT" | jq '.repo_mapping' | jq -r length)" -eq 2
test "$(echo "$OUTPUT" | jq '.repo_mapping.src1')" = "\"dest1\""
test "$(echo "$OUTPUT" | jq '.repo_mapping.src2')" = "\"dest2\""
