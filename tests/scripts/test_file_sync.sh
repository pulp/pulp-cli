#!/bin/sh

. "$(dirname "$(realpath "$0")")/config.source"
. "$(dirname "$(realpath "$0")")/constants.source"

cleanup() {
  pulp_cli file remote destroy --name "cli_test_file_remote" || true
  pulp_cli file repository destroy --name "cli_test_file_repository" || true
}
trap cleanup EXIT

# Prepare
pulp_cli file remote create --name "cli_test_file_remote" --url "$FILE_REMOTE_URL"
pulp_cli file repository create --name "cli_test_file_repository"

# Test without remote (should fail)
! pulp_cli file repository sync --name "cli_test_file_repository"
# Test with remote
pulp_cli file repository sync --name "cli_test_file_repository" --remote "cli_test_file_remote"

# Preconfigure remote
pulp_cli file repository update --name "cli_test_file_repository" --remote "cli_test_file_remote"

# Test with remote
pulp_cli file repository sync --name "cli_test_file_repository"
# Test without remote
pulp_cli file repository sync --name "cli_test_file_repository" --remote "cli_test_file_remote"

# Verify sync
test "$(pulp_cli file repository version list --repository "cli_test_file_repository" | jq -r .count)" -eq 2
