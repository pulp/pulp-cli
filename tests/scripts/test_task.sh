#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")/config.source"

cleanup() {
  pulp_cli file remote destroy --name "cli_test_file_remote" || true
  pulp_cli file remote destroy --name "cli_test_file_large_remote" || true
  pulp_cli file repository destroy --name "cli_test_file_repository" || true
  pulp_cli orphans delete || true
}
trap cleanup EXIT

sync_task="pulp_file.app.tasks.synchronizing.synchronize"
count=$(pulp_cli task list --name $sync_task --state canceled | jq -r length)

pulp_cli file remote create --name "cli_test_file_remote" \
  --url "https://fixtures.pulpproject.org/file/PULP_MANIFEST"
pulp_cli file remote create --name "cli_test_file_large_remote" \
  --url "https://fixtures.pulpproject.org/file-large/PULP_MANIFEST"
pulp_cli file repository create --name "cli_test_file_repository" --remote "cli_test_file_large_remote"

# Test canceling a task
task=$(pulp_cli file repository sync --background --name "cli_test_file_repository" 2>&1 | grep -E -o "/pulp/api/v3/tasks/[-[:xdigit:]]*/")
pulp_cli task cancel --href "$task"
test "$(pulp_cli task list --name $sync_task --state canceled | jq -r length)" -eq $((count + 1))
test "$(pulp_cli task show --href "$task" | jq -r '.state')" = "canceled"

# Test waiting for a task
task=$(pulp_cli file repository sync --background --name "cli_test_file_repository" --remote "cli_test_file_remote" 2>&1 | grep -E -o "/pulp/api/v3/tasks/[-[:xdigit:]]*/")
test "$(pulp_cli task show --wait --href "$task" | jq -r '.state')" = "completed"

pulp_cli task list --name-contains file

test "$(pulp_cli task list --limit 1 | jq -r length)" -eq 1
