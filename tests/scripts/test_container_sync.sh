#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")/config.source"

cleanup() {
  pulp container remote --name "cli_test_container_remote" destroy || true
  pulp container repository --name "cli_test_container_repository" destroy || true
}
trap cleanup EXIT

# Prepare
pulp container remote create --name "cli_test_container_remote" --url "$CONTAINER_REMOTE_URL" --upstream-name "$CONTAINER_IMAGE"
pulp container repository create --name "cli_test_container_repository"

# Test without remote (should fail)
expect_fail pulp container repository --name "cli_test_container_repository" sync
# Test with remote
expect_succ pulp container repository --name "cli_test_container_repository" sync --remote "cli_test_container_remote"

# Preconfigure remote
# TBD
# pulp container repository --name "cli_test_container_repository" update --remote "cli_test_container_remote"

# Test without remote
# expect_succ pulp container repository --name "cli_test_container_repository" sync
# Test with remote
# expect_succ pulp container repository --name "cli_test_container_repository" sync --remote "cli_test_container_remote"

# Verify sync
expect_succ pulp container repository --name "cli_test_container_repository" version list
test "$(echo "$OUTPUT" | jq -r length)" -eq 2
expect_succ pulp container repository --name "cli_test_container_repository" version show --version 1
test "$(echo "$OUTPUT" | jq -r '.content_summary.present."container.tag".count')" -gt 0

# Delete version again
expect_succ pulp container repository --name "cli_test_container_repository" version destroy --version 1
