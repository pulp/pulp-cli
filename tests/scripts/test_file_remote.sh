#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")/config.source"

cleanup() {
  pulp_cli file remote destroy --name "cli_test_file_remote" || true
}
trap cleanup EXIT

expect_succ pulp file remote list

expect_succ pulp file remote create --name "cli_test_file_remote" --url "$FILE_REMOTE_URL"
expect_succ pulp file remote list
expect_succ pulp file remote destroy --name "cli_test_file_remote"
