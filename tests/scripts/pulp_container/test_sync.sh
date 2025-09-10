#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "container" || exit 23

cleanup() {
  pulp container repository destroy --name "cli_test_container_sync_repository" || true
  pulp container remote destroy --name "cli_test_container_sync_remote" || true
}
trap cleanup EXIT

# Prepare
pulp container remote create --name "cli_test_container_sync_remote" --url "$CONTAINER_REMOTE_URL" --upstream-name "$CONTAINER_IMAGE"
pulp container repository create --name "cli_test_container_sync_repository"

# Test without remote (should fail)
expect_fail pulp container repository sync --repository "cli_test_container_sync_repository"
# Test with remote
expect_succ pulp container repository sync --repository "cli_test_container_sync_repository" --remote "cli_test_container_sync_remote"

# Preconfigure remote
# TBD
# pulp container repository update --name "cli_test_container_sync_repository" --remote "cli_test_container_sync_remote"

# Test with remote
# expect_succ pulp container repository sync --name "cli_test_container_sync_repository"
# Test without remote
# expect_succ pulp container repository sync --name "cli_test_container_sync_repository" --remote "cli_test_container_sync_remote"

# Verify sync
expect_succ pulp container repository version list --repository "cli_test_container_sync_repository"
test "$(echo "$OUTPUT" | jq -r length)" -eq 2
expect_succ pulp container repository version show --repository "cli_test_container_sync_repository" --version 1
test "$(echo "$OUTPUT" | jq -r '.content_summary.present."container.tag".count')" -gt 0

# Delete version again
expect_succ pulp container repository version destroy --repository "cli_test_container_sync_repository" --version 1
