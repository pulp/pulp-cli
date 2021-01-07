#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")/config.source"

cleanup() {
  pulp file remote destroy --name "cli_test_file_remote" || true
  pulp file repository destroy --name "cli_test_file_repository" || true
}
trap cleanup EXIT

cleanup

# Prepare
expect_succ pulp file remote create --name "cli_test_file_remote" --url "$FILE_REMOTE_URL"
expect_succ pulp file repository create --name "cli_test_file_repository"

# Test without remote (should fail)
expect_fail pulp file repository sync --name "cli_test_file_repository"
# Test with remote
expect_succ pulp file repository sync --name "cli_test_file_repository" --remote "cli_test_file_remote"

# Preconfigure remote
expect_succ pulp file repository update --name "cli_test_file_repository" --remote "cli_test_file_remote"

# Test with remote
expect_succ pulp file repository sync --name "cli_test_file_repository"
# Test without remote
expect_succ pulp file repository sync --name "cli_test_file_repository" --remote "cli_test_file_remote"

# Verify sync
expect_succ pulp file repository version --repository "cli_test_file_repository" list
test "$(echo "$OUTPUT" | jq -r length)" -eq 2
expect_succ pulp file repository version --repository "cli_test_file_repository" show --version 1
test "$(echo "$OUTPUT" | jq -r '.content_summary.present."file.file".count')" -eq 3

# Test repair the version
expect_succ pulp file repository version --repository "cli_test_file_repository" repair --version 1
test "$(echo "$OUTPUT" | jq -r '.state')" = "completed"

# Delete version again
expect_succ pulp file repository version --repository "cli_test_file_repository" destroy --version 1
