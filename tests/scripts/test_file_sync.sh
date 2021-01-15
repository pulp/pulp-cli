#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")/config.source"

cleanup() {
  pulp file remote destroy --name "cli_test_file_remote" || true
  pulp file repository --name "cli_test_file_repository" destroy || true
}
trap cleanup EXIT

cleanup

# Prepare
expect_succ pulp file remote create --name "cli_test_file_remote" --url "$FILE_REMOTE_URL"
expect_succ pulp file repository create --name "cli_test_file_repository"

# Test without remote (should fail)
expect_fail pulp file repository --name "cli_test_file_repository" sync
# Test with remote
expect_succ pulp file repository --name "cli_test_file_repository" sync --remote "cli_test_file_remote"

# Preconfigure remote
expect_succ pulp file repository --name "cli_test_file_repository" update --remote "cli_test_file_remote"

# Test without remote
expect_succ pulp file repository --name "cli_test_file_repository" sync
# Test with remote
expect_succ pulp file repository --name "cli_test_file_repository" sync --remote "cli_test_file_remote"

# Verify sync
expect_succ pulp file repository --name "cli_test_file_repository" version list
test "$(echo "$OUTPUT" | jq -r length)" -eq 2
expect_succ pulp file repository --name "cli_test_file_repository" version show --version 1
test "$(echo "$OUTPUT" | jq -r '.content_summary.present."file.file".count')" -eq 3

# Test repair the version
expect_succ pulp file repository --name "cli_test_file_repository" version repair --version 1
test "$(echo "$OUTPUT" | jq -r '.state')" = "completed"

# Delete version again
expect_succ pulp file repository --name "cli_test_file_repository" version destroy --version 1
