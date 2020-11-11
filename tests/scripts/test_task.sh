#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")/config.source"

cleanup() {
  pulp file remote destroy --name "cli_test_file_remote" || true
  pulp file remote destroy --name "cli_test_file_large_remote" || true
  pulp file repository destroy --name "cli_test_file_repository" || true
  pulp orphans delete || true
}
trap cleanup EXIT

sync_task="pulp_file.app.tasks.synchronizing.synchronize"
expect_succ pulp task list --name $sync_task --state canceled
count="$(echo "$OUTPUT" | jq -r length)"

expect_succ pulp file remote create --name "cli_test_file_remote" \
  --url "https://fixtures.pulpproject.org/file/PULP_MANIFEST"
expect_succ pulp file remote create --name "cli_test_file_large_remote" \
  --url "https://fixtures.pulpproject.org/file-large/PULP_MANIFEST"
expect_succ pulp file repository create --name "cli_test_file_repository" --remote "cli_test_file_large_remote"

# Test canceling a task
expect_succ pulp --background file repository sync --name "cli_test_file_repository"
task="$(echo "$ERROUTPUT" | grep -E -o "/pulp/api/v3/tasks/[-[:xdigit:]]*/")"
expect_succ pulp task cancel --href "$task"
expect_succ pulp task list --name $sync_task --state canceled
expect_succ test "$(echo "$OUTPUT" | jq -r length)" -eq $((count + 1))
expect_succ pulp task show --href "$task"
expect_succ test "$(echo "$OUTPUT" | jq -r '.state')" = "canceled"

# Test waiting for a task
expect_succ pulp --background file repository sync --name "cli_test_file_repository" --remote "cli_test_file_remote"
task=$(echo "$ERROUTPUT" | grep -E -o "/pulp/api/v3/tasks/[-[:xdigit:]]*/")
expect_succ pulp task show --wait --href "$task"
expect_succ test "$(echo "$OUTPUT" | jq -r '.state')" = "completed"

expect_succ pulp task list --name-contains file

expect_succ pulp task list --limit 1
expect_succ test "$(echo "$OUTPUT" | jq -r length)" -eq 1
