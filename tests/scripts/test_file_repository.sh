#!/bin/sh

. "$(dirname "$(realpath $0)")/config.sh"

pulp_cli file repository list

pulp_cli file repository create --name "cli_test_file_repo"
pulp_cli file repository destroy --name "cli_test_file_repo"
