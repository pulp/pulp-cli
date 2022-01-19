#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "file" || exit 3

cleanup() {
  pulp file remote destroy --name "cli_test_file_remote" || true
  pulp file remote destroy --name "cli_test_file_large_remote" || true
  pulp file repository destroy --name "cli_test_file_repository" || true
  pulp orphan cleanup || true
}
trap cleanup EXIT

sync_task="pulp_file.app.tasks.synchronizing.synchronize"
expect_succ pulp task list --name $sync_task --state canceled
count="$(echo "$OUTPUT" | jq -r length)"

expect_succ pulp file remote create --name "cli_test_file_remote" \
  --url "$FILE_REMOTE_URL"
expect_succ pulp file remote create --name "cli_test_file_large_remote" \
  --url "$FILE_LARGE_REMOTE_URL"
expect_succ pulp file repository create --name "cli_test_file_repository" --remote "cli_test_file_large_remote"

# Test canceling a task
if pulp debug has-plugin --name "core" --min-version "3.12.0"
then
  expect_succ pulp --background file repository sync --name "cli_test_file_repository"
  task="$(echo "$ERROUTPUT" | grep -E -o "/pulp/api/v3/tasks/[-[:xdigit:]]*/")"
  expect_succ pulp task cancel --href "$task"
  expect_succ pulp task list --name $sync_task --state canceled
  expect_succ test "$(echo "$OUTPUT" | jq -r length)" -eq $((count + 1))
  expect_succ pulp task show --href "$task"
  expect_succ test "$(echo "$OUTPUT" | jq -r '.state')" = "canceled"
fi

# Test waiting for a task
expect_succ pulp --background file repository sync --name "cli_test_file_repository" --remote "cli_test_file_remote"
task=$(echo "$ERROUTPUT" | grep -E -o "/pulp/api/v3/tasks/[-[:xdigit:]]*/")
task_uuid="${task%/}"
task_uuid="${task_uuid##*/}"
expect_succ pulp task show --wait --uuid "$task_uuid"
expect_succ test "$(echo "$OUTPUT" | jq -r '.state')" = "completed"

expect_succ pulp task list --name-contains file

expect_fail pulp task list --state=cannotwork
expect_succ pulp task list --state=COmPLetED
expect_succ test "$(echo "$OUTPUT" | jq -r '.[0].state')" = "completed"

expect_succ pulp task list --limit 1
expect_succ test "$(echo "$OUTPUT" | jq -r length)" -eq 1

# Test purging tasks
if pulp debug has-plugin --name core --min-version 3.17.0.dev
then
  expect_succ pulp task purge
  expect_succ pulp task purge --finished-before "2021-12-01" --state "failed"
  expect_succ pulp task purge --finished-before "2021-12-01T12:00:00" --state "completed" --state "failed"
  expect_fail pulp task purge --finished-before "NOT A DATE"
  expect_fail pulp task purge --finished-before "2021-12-01T12:00:00" --state "NOT A STATE"
  expect_fail pulp task purge --finished-before "2021-12-01T12:00:00" --state "running"
fi
