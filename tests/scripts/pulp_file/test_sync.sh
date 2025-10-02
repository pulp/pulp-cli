#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "file" || exit 23

autopublish_repo="cli_test_file_sync_repository_autopublish"
one_version_repo="cli_test_one_version_repo"

cleanup() {
  pulp file repository destroy --name "cli_test_file_sync_repository" || true
  pulp file repository destroy --name "$autopublish_repo" || true
  pulp file repository destroy --name "$one_version_repo" || true
  pulp file remote destroy --name "cli_test_file_sync_remote" || true
}
trap cleanup EXIT

cleanup

# Prepare
expect_succ pulp file remote create --name "cli_test_file_sync_remote" --url "$FILE_REMOTE_URL"
expect_succ pulp file repository create --name "cli_test_file_sync_repository"

# Test without remote (should fail)
expect_fail pulp file repository sync --repository "cli_test_file_sync_repository"
# Test with remote
expect_succ pulp file repository sync --repository "cli_test_file_sync_repository" --remote "cli_test_file_sync_remote"

# Preconfigure remote
expect_succ pulp file repository update --repository "cli_test_file_sync_repository" --remote "cli_test_file_sync_remote"

# Test with remote
expect_succ pulp file repository sync --repository "cli_test_file_sync_repository"
# Test without remote
expect_succ pulp file repository sync --repository "cli_test_file_sync_repository" --remote "cli_test_file_sync_remote"

# Verify sync
expect_succ pulp file repository version list --repository "cli_test_file_sync_repository"
test "$(echo "$OUTPUT" | jq -r length)" -eq 2
expect_succ pulp file repository version show --repository "cli_test_file_sync_repository" --version 1
test "$(echo "$OUTPUT" | jq -r '.content_summary.present."file.file".count')" -eq 3

# Test repair the version
expect_succ pulp file repository version repair --repository "cli_test_file_sync_repository" --version 1
test "$(echo "$OUTPUT" | jq -r '.state')" = "completed"

# Delete version again
expect_succ pulp file repository version destroy --version 1 --repository "cli_test_file_sync_repository"

# Test autopublish
expect_succ pulp file repository create --name "$autopublish_repo" --remote "cli_test_file_sync_remote" --autopublish
expect_succ pulp file repository sync --repository "$autopublish_repo"
task=$(echo "$ERROUTPUT" | grep -E -o "${PULP_API_ROOT}([-_a-zA-Z0-9]+/)?api/v3/tasks/[-[:xdigit:]]*/")
created_resources=$(pulp show --href "$task" | jq -r ".created_resources")
echo "$created_resources" | grep -q -E "${PULP_API_ROOT}([-_a-zA-Z0-9]+/)?api/v3/publications/file/file/"

# Test retained versions
expect_succ pulp file repository create --name "$one_version_repo" --remote "cli_test_file_sync_remote" --retain-repo-versions 1
expect_succ pulp file repository sync --repository "$one_version_repo"
expect_succ pulp file repository version list --repository "$one_version_repo"
test "$(echo "$OUTPUT" | jq -r length)" -eq 1
