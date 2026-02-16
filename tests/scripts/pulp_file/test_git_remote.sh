#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "file" --specifier ">=3.104.0" || exit 23

GIT_REMOTE_URL="${GIT_REMOTE_URL:-https://github.com/pulp/pulp-fixtures.git}"

cleanup() {
  pulp file repository destroy --name "cli_test_file_git_repo" || true
  pulp file remote --type git destroy --name "cli_test_file_git_remote" || true
}
trap cleanup EXIT

cleanup

expect_succ pulp file remote --type git list

expect_succ pulp file remote --type git create \
  --name "cli_test_file_git_remote" \
  --url "$GIT_REMOTE_URL" \
  --git-ref main
HREF="$(echo "$OUTPUT" | jq -r '.pulp_href')"
remote_prn="$(echo "$OUTPUT" | jq -r '.prn')"
test "$(echo "$OUTPUT" | jq -r '.git_ref')" = "main"

expect_succ pulp file remote --type git show --remote "cli_test_file_git_remote"
expect_succ pulp file remote --type git show --remote "$HREF"
expect_succ pulp file remote --type git show --remote "${remote_prn}"

expect_succ pulp file remote --type git list --name-contains "cli_test_file_git"
test "$(echo "$OUTPUT" | jq -r '.[0].name')" = "cli_test_file_git_remote"

expect_succ pulp file remote --type git update --remote "$HREF" --git-ref master
expect_succ pulp file remote --type git show --remote "cli_test_file_git_remote"
test "$(echo "$OUTPUT" | jq -r '.git_ref')" = "master"

expect_succ pulp file repository create --name "cli_test_file_git_repo"
expect_succ pulp file repository update \
  --repository "cli_test_file_git_repo" \
  --remote "file:git:cli_test_file_git_remote"
expect_succ pulp file repository show --repository "cli_test_file_git_repo"
test "$(echo "$OUTPUT" | jq -r '.remote')" = "$HREF"

expect_succ pulp file remote --type git destroy --name "cli_test_file_git_remote"
