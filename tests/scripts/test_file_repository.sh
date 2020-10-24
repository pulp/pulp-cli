#!/bin/sh

. "$(dirname "$(realpath "$0")")/config.source"

pulp_cli file repository list

pulp_cli file repository create --name "cli_test_file_repo"
pulp_cli file repository update --name "cli_test_file_repo" --description "Test repository for CLI tests"
pulp_cli file repository list
pulp_cli file repository destroy --name "cli_test_file_repo"
