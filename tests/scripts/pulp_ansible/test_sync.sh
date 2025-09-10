#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "ansible" || exit 23

cleanup() {
  pulp ansible remote -t "role" destroy --name "cli_test_ansible_sync_role_remote" || true
  pulp ansible remote -t "collection" destroy --name "cli_test_ansible_sync_remote" || true
  pulp ansible repository destroy --name "cli_test_ansible_sync_repository" || true
}
trap cleanup EXIT

cleanup

# Prepare
expect_succ pulp ansible remote -t "role" create --name "cli_test_ansible_sync_role_remote" --url "$ANSIBLE_ROLE_REMOTE_URL"
expect_succ pulp ansible remote -t "collection" create --name "cli_test_ansible_sync_remote" \
--url "$ANSIBLE_COLLECTION_REMOTE_URL" --requirements "collections:
  - robertdebock.ansible_development_environment"
expect_succ pulp ansible repository create --name "cli_test_ansible_sync_repository"

# Test without remote (should fail)
expect_fail pulp ansible repository sync --repository "cli_test_ansible_sync_repository"
# Test with remote
expect_succ pulp ansible repository sync --repository "cli_test_ansible_sync_repository" --remote "role:cli_test_ansible_sync_role_remote"

# Preconfigure remote
expect_succ pulp ansible repository update --repository "cli_test_ansible_sync_repository" --remote "role:cli_test_ansible_sync_role_remote"

# Test with remote
expect_succ pulp ansible repository sync --repository "cli_test_ansible_sync_repository"
# Test without remote
expect_succ pulp ansible repository sync --repository "cli_test_ansible_sync_repository" --remote "role:cli_test_ansible_sync_role_remote"

# Verify sync
expect_succ pulp ansible repository version list --repository "cli_test_ansible_sync_repository"
test "$(echo "$OUTPUT" | jq -r length)" -eq 2
expect_succ pulp ansible repository version show --repository "cli_test_ansible_sync_repository" --version 1
test "$(echo "$OUTPUT" | jq -r '.content_summary.present."ansible.role".count')" -gt 0
expect_succ pulp ansible content --type role list
test "$(echo "$OUTPUT" | jq -r length)" -gt 0

# Test repair the version
expect_succ pulp ansible repository version repair --repository "cli_test_ansible_sync_repository" --version 1
test "$(echo "$OUTPUT" | jq -r '.state')" = "completed"

# Delete version again
expect_succ pulp ansible repository version destroy --repository "cli_test_ansible_sync_repository" --version 1

# Test with collection remote
expect_succ pulp ansible repository sync --name "cli_test_ansible_sync_repository" --remote "cli_test_ansible_sync_remote"

# Verify sync
expect_succ pulp ansible repository version list --repository "cli_test_ansible_sync_repository"
test "$(echo "$OUTPUT" | jq -r length)" -eq 2
expect_succ pulp ansible repository version show --repository "cli_test_ansible_sync_repository" --version 2
test "$(echo "$OUTPUT" | jq -r '.content_summary.present."ansible.collection_version".count')" -gt 0
expect_succ pulp ansible content list
test "$(echo "$OUTPUT" | jq -r length)" -gt 0
