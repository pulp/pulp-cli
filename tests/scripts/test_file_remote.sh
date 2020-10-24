#!/bin/sh

. "$(dirname "$(realpath "$0")")/config.source"
. "$(dirname "$(realpath "$0")")/constants.source"

pulp_cli file remote list

pulp_cli file remote create --name "cli_test_file_remote" --url "$FILE_REMOTE_URL"
pulp_cli file remote list
pulp_cli file remote destroy --name "cli_test_file_remote"
