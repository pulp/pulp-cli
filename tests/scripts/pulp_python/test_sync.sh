#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "python" || exit 3

cleanup() {
  pulp python repository destroy --name "cli_test_python_repository" || true
  pulp python remote destroy --name "cli_test_python_remote" || true
  pulp orphan cleanup || true
}
trap cleanup EXIT

cleanup

# Prepare
expect_succ pulp python remote create --name "cli_test_python_remote" --url "$PYTHON_REMOTE_URL" \
  --includes '["shelf-reader", "aiohttp>=3.2.0,<3.3.1", "celery~=4.0", "Django>1.10.0,<=2.0.6"]'
expect_succ pulp python repository create --name "cli_test_python_repository"

# Test without remote (should fail)
expect_fail pulp python repository sync --name "cli_test_python_repository"
# Test with remote
expect_succ pulp python repository sync --name "cli_test_python_repository" --remote "cli_test_python_remote"

# Preconfigure remote
expect_succ pulp python repository update --name "cli_test_python_repository" --remote "cli_test_python_remote"

# Test with remote
expect_succ pulp python repository sync --name "cli_test_python_repository"

# Verify sync
expect_succ pulp python repository version list --repository "cli_test_python_repository"
expect_succ test "$(echo "$OUTPUT" | jq -r length)" -eq 2
expect_succ pulp python repository version show --repository "cli_test_python_repository" --version 1
expect_succ test "$(echo "$OUTPUT" | jq -r '.content_summary.present."python.python".count')" -eq 34

# Test repair the version
expect_succ pulp python repository version repair --repository "cli_test_python_repository" --version 1
expect_succ test "$(echo "$OUTPUT" | jq -r '.state')" = "completed"

# Delete version again
expect_succ pulp python repository version destroy --repository "cli_test_python_repository" --version 1
