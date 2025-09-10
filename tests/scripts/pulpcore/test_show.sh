#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "file" || exit 23

cleanup() {
  pulp file repository destroy --name "cli_test_core_show_repo" || true
  pulp file remote destroy --name "cli_test_core_show_remote" || true
}
trap cleanup EXIT

expect_succ pulp file repository create --name "cli_test_core_show_repo"
repo_href="$(echo "$OUTPUT" | jq -r .pulp_href)"
expect_succ pulp show --href "$repo_href"

expect_succ pulp file remote create --name "cli_test_core_show_remote" --url "$FILE_REMOTE_URL"
remote_href="$(echo "$OUTPUT" | jq -r .pulp_href)"
expect_succ pulp show --href "$remote_href"
