#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "rust" || exit 23

cleanup() {
  pulp rust remote destroy --name "cli_test_rust_remote" || true
}
trap cleanup EXIT

expect_succ pulp rust remote list

expect_succ pulp rust remote create --name "cli_test_rust_remote" --url "sparse+https://index.crates.io/" --policy "on_demand"
expect_succ pulp rust remote show --remote "cli_test_rust_remote"
HREF="$(echo "$OUTPUT" | jq -r '.pulp_href')"
test "$(echo "$OUTPUT" | jq -r '.policy')" = "on_demand"

expect_succ pulp rust remote update --remote "$HREF" --policy "streamed"
expect_succ pulp rust remote show --remote "cli_test_rust_remote"
test "$(echo "$OUTPUT" | jq -r '.policy')" = "streamed"

expect_succ pulp rust remote list --name-contains "cli_test_rust"
test "$(echo "$OUTPUT" | jq -r length)" -ge 1

expect_succ pulp rust remote destroy --name "cli_test_rust_remote"
