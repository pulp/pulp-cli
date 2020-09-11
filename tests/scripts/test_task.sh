#!/bin/sh

. "$(dirname "$(realpath $0)")/config.sh"

cleanup() {
  pulp_cli file remote destroy --name "cli_test_file_remote"
  pulp_cli file repository destroy --name "cli_test_file_repository"
  pulp_cli orphans delete
}
trap cleanup EXIT

sync_task="pulp_file.app.tasks.synchronizing.synchronize"
count=$(pulp_cli task list --name $sync_task --state canceled | jq -r .count)

pulp_cli file remote create --name "cli_test_file_remote" \
  --url "https://fixtures.pulpproject.org/file-large/PULP_MANIFEST"
pulp_cli file repository create --name "cli_test_file_repository" --remote "cli_test_file_remote"

task=$(pulp_cli file repository sync --background --name "cli_test_file_repository" 2>&1 | egrep -o "/.*/")
pulp_cli task cancel --href "$task"
test $(pulp_cli task list --name $sync_task --state canceled | jq -r .count) -eq $(($count + 1))

pulp_cli task list --name-contains file
