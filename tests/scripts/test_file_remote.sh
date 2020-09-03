#!/bin/sh

. "$(dirname "$(realpath $0)")/config.sh"
. "$(dirname "$(realpath $0)")/constants.sh"

pulp_cli file remote list

pulp_cli file remote create --name "cli_test_file_remote" --url "$FILE_REMOTE_URL"
pulp_cli file remote list
pulp_cli file remote destroy --name "cli_test_file_remote"
