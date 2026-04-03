#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "rust" || exit 23

cleanup() {
  pulp rust distribution destroy --name "cli_test_rust_distro" || true
  pulp rust repository destroy --name "cli_test_rust_distro_repo" || true
  pulp rust remote destroy --name "cli_test_rust_distro_remote" || true
}
trap cleanup EXIT

expect_succ pulp rust remote create --name "cli_test_rust_distro_remote" --url "sparse+https://index.crates.io/"
expect_succ pulp rust repository create --name "cli_test_rust_distro_repo" --remote "cli_test_rust_distro_remote"

expect_succ pulp rust distribution create \
  --name "cli_test_rust_distro" \
  --base-path "cli_test_rust_distro" \
  --repository "cli_test_rust_distro_repo"

expect_succ pulp rust distribution show --distribution "cli_test_rust_distro"
test "$(echo "$OUTPUT" | jq -r '.base_path')" = "cli_test_rust_distro"

expect_succ pulp rust distribution update \
  --distribution "cli_test_rust_distro" \
  --base-path "cli_test_rust_distro_updated"
expect_succ pulp rust distribution show --distribution "cli_test_rust_distro"
test "$(echo "$OUTPUT" | jq -r '.base_path')" = "cli_test_rust_distro_updated"

expect_succ pulp rust distribution list --base-path "cli_test_rust_distro_updated"
test "$(echo "$OUTPUT" | jq -r length)" -eq 1

expect_succ pulp rust distribution destroy --distribution "cli_test_rust_distro"
