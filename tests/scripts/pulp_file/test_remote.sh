#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "file" || exit 3

cleanup() {
  pulp file remote destroy --name "cli_test_file_remote" || true
}
trap cleanup EXIT

expect_succ pulp file remote list

expect_succ pulp file remote create --name "cli_test_file_remote" --url "$FILE_REMOTE_URL" --proxy-url "http://proxy.org" --proxy-username "user" --proxy-password "pass"
expect_succ pulp file remote show --name "cli_test_file_remote"
expect_succ pulp file remote list

# test ref option
expect_succ pulp file remote update --ref "cli_test_file_remote" --url "test"
expect_succ pulp file remote show -r "cli_test_file_remote"
href=$(echo "$OUTPUT" | jq -r ".pulp_href")
expect_succ pulp file remote show -r "$href"

expect_succ pulp file remote destroy --name "cli_test_file_remote"
