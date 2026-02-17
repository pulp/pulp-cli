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
REPO_HREF="$(echo "$OUTPUT" | jq -r .pulp_href)"
expect_succ pulp show --href "$REPO_HREF"

expect_succ pulp file remote create --name "cli_test_core_show_remote" --url "$FILE_REMOTE_URL"
REMOTE_HREF="$(echo "$OUTPUT" | jq -r .pulp_href)"
REMOTE_PRN="$(echo "$OUTPUT" | jq -r .prn)"
expect_succ pulp show --href "$REMOTE_HREF"
if pulp debug has-plugin --name core --specifier ">=3.63.0"
then
  expect_succ pulp show --prn "$REMOTE_PRN"
fi
