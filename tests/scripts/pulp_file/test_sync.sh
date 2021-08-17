#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "file" || exit 3

autopublish_repo="cli_test_file_repository_autopublish"
one_version_repo="cli_test_one_version_repo"

cleanup() {
  pulp file remote destroy --name "cli_test_file_remote" || true
  pulp file repository destroy --name "cli_test_file_repository" || true
  pulp file repository destroy --name "$autopublish_repo" || true
  pulp file repository destroy --name "$one_version_repo" || true
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
expect_succ pulp file repository version list --repository "cli_test_file_repository"
test "$(echo "$OUTPUT" | jq -r length)" -eq 2
expect_succ pulp file repository version show --repository "cli_test_file_repository" --version 1
test "$(echo "$OUTPUT" | jq -r '.content_summary.present."file.file".count')" -eq 3

# Test repair the version
expect_succ pulp file repository version repair --repository "cli_test_file_repository" --version 1
test "$(echo "$OUTPUT" | jq -r '.state')" = "completed"

# Delete version again
expect_succ pulp file repository version destroy --repository "cli_test_file_repository" --version 1

# Test autopublish
if [ "$(pulp debug has-plugin --name "file" --min-version "1.7.0.dev")" = "true" ]
then
  expect_succ pulp file repository create --name "$autopublish_repo" --remote "cli_test_file_remote" --autopublish
  expect_succ pulp file repository sync --name "$autopublish_repo"
  task=$(echo "$ERROUTPUT" | grep -E -o "/pulp/api/v3/tasks/[-[:xdigit:]]*/")
  created_resources=$(pulp show --href "$task" | jq -r ".created_resources")
  echo "$created_resources" | grep -q '/pulp/api/v3/publications/file/file/'
fi

# Test retained versions
if [ "$(pulp debug has-plugin --name "core" --min-version "3.13.0.dev")" = "true" ]
then
  expect_succ pulp file repository create --name "$one_version_repo" --remote "cli_test_file_remote" --retain-repo-versions 1
  expect_succ pulp file repository sync --name "$one_version_repo"
  expect_succ pulp file repository version list --repository "$one_version_repo"
  test "$(echo "$OUTPUT" | jq -r length)" -eq 1
fi
