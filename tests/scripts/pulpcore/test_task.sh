#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "file" || exit 23

cleanup() {
  pulp file repository destroy --name "cli_test_core_task_repository" || true
  pulp file remote destroy --name "cli_test_core_task_remote" || true
  pulp file remote destroy --name "cli_test_core_task_large_remote" || true
}
trap cleanup EXIT


expected_repo_task_count=1
sync_task="pulp_file.app.tasks.synchronizing.synchronize"
expect_succ pulp task list --name $sync_task --state canceled
count="$(echo "$OUTPUT" | jq -r length)"
expect_succ pulp worker list --limit 1
worker="$(echo "$OUTPUT" | jq -r '.[0].pulp_href')"
worker_name="$(echo "$OUTPUT" | jq -r '.[0].name')"

expect_succ pulp file remote create --name "cli_test_core_task_remote" --url "$FILE_REMOTE_URL"
remote_href="$(echo "$OUTPUT" | jq -r '.pulp_href')"
expect_succ pulp file remote create --name "cli_test_core_task_large_remote" --url "$FILE_LARGE_REMOTE_URL"
expect_succ pulp file repository create --name "cli_test_core_task_repository" --remote "cli_test_core_task_remote"
repository_href="$(echo "$OUTPUT" | jq -r '.pulp_href')"

# Test canceling a task introduced in 3.12, but not reliable in 3.18
if pulp debug has-plugin --name "core" --specifier ">=3.21.0"
then
  expect_succ pulp --background file repository sync --name "cli_test_core_task_repository" --remote "cli_test_core_task_large_remote"
  task="$(echo "$ERROUTPUT" | grep -E -o "${PULP_API_ROOT}([-_a-zA-Z0-9]+/)?api/v3/tasks/[-[:xdigit:]]*/")"
  if expect_succ pulp task cancel --href "$task"
  then
    expect_succ pulp task list --name $sync_task --state canceled
    expect_succ test "$(echo "$OUTPUT" | jq -r length)" -eq $((count + 1))
    expect_succ pulp task show --href "$task"
    expect_succ test "$(echo "$OUTPUT" | jq -r '.state')" = "canceled"
  else
    expect_succ pulp task list --name $sync_task --state canceled
    expect_succ test "$(echo "$OUTPUT" | jq -r length)" -eq $((count + 0))
    expect_succ pulp task show --href "$task"
    expect_succ test "$(echo "$OUTPUT" | jq -r '.state')" = "completed"
  fi
  expected_repo_task_count=$((expected_repo_task_count + 1))
fi

expect_fail pulp --dry-run task cancel --all

# Test waiting for a task
expect_succ pulp --background file repository sync --name "cli_test_core_task_repository"
task=$(echo "$ERROUTPUT" | grep -E -o "${PULP_API_ROOT}([-_a-zA-Z0-9]+/)?api/v3/tasks/[-[:xdigit:]]*/")
task_uuid="${task%/}"
task_uuid="${task_uuid##*/}"
expect_succ pulp task show --wait --uuid "$task_uuid"
created_resource="$(echo "$OUTPUT" | jq -r '.created_resources[0]')"
expect_succ test "$(echo "$OUTPUT" | jq -r '.state')" = "completed"

expect_succ pulp task list --name-contains file
expect_succ pulp task list --parent-task "$task" --worker "$worker"
expect_succ pulp task list --parent-task "$task_uuid" --worker "$worker_name"
expect_succ pulp task list --started-before "21/01/12" --started-after "22/01/06T00:00:00"
expect_succ pulp task list --finished-before "2021-12-01" --finished-after "2022-06-01 00:00:00"
expect_succ pulp task list --created-resource "$created_resource"

if pulp debug has-plugin --name "core" --specifier ">=3.22.0"
then
  # New style task resource filters
  expect_succ pulp task list --reserved-resource-in "$repository_href" --reserved-resource-in "$remote_href"
  expect_succ test "$(echo "$OUTPUT" | jq -r length)" -eq 1
  expect_succ pulp task list --reserved-resource "$repository_href"
  expect_succ test "$(echo "$OUTPUT" | jq -r length)" -eq 2
  expect_succ pulp task list --exclusive-resource "$repository_href"
  expect_succ test "$(echo "$OUTPUT" | jq -r length)" -eq 2
  expect_succ pulp task list --exclusive-resource "$remote_href"
  expect_succ test "$(echo "$OUTPUT" | jq -r length)" -eq 0
  expect_succ pulp task list --shared-resource "$remote_href"
  expect_succ test "$(echo "$OUTPUT" | jq -r length)" -eq 1
else
  expect_succ pulp task list --reserved-resource "$repository_href"
  expect_succ test "$(echo "$OUTPUT" | jq -r length)" -eq "$expected_repo_task_count"
fi

expect_fail pulp task list --state=cannotwork
expect_succ pulp task list --state=COmPLetED
expect_succ test "$(echo "$OUTPUT" | jq -r '.[0].state')" = "completed"

expect_succ pulp task list --limit 1
expect_succ test "$(echo "$OUTPUT" | jq -r length)" -eq 1

# Test purging tasks
expect_succ pulp task purge
expect_succ pulp task purge --finished-before "2021-12-01" --state "failed"
expect_succ pulp task purge --finished-before "2021-12-01T12:00:00" --state "completed" --state "failed"
expect_fail pulp task purge --finished-before "NOT A DATE"
expect_fail pulp task purge --finished-before "2021-12-01T12:00:00" --state "NOT A STATE"
expect_fail pulp task purge --finished-before "2021-12-01T12:00:00" --state "running"

# Test task summary
expect_succ pulp task summary
