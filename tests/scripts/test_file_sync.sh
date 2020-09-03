#!/bin/sh

. "$(dirname "$(realpath $0)")/config.sh"
. "$(dirname "$(realpath $0)")/constants.sh"

pulp_cli file remote create --name "cli_test_file_remote" --url "$FILE_REMOTE_URL"
pulp_cli file repository create --name "cli_test_file_repository" --remote "cli_test_file_remote"

pulp_cli file repository sync --name "cli_test_file_repository"
pulp_cli file repository sync --name "cli_test_file_repository" --remote "cli_test_file_remote"

pulp_cli file remote destroy --name "cli_test_file_remote"
pulp_cli file repository destroy --name "cli_test_file_repository"
