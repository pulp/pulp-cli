#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")/config.source"

pulp debug has-plugin --name "pulpcore" --min-version "3.10.dev" || exit 3

cleanup() {
  pulp group destroy --name "cli_test_group" || true
  pulp file repository destroy --name "cli_group_test_repository" || true
}
trap cleanup EXIT

expect_succ pulp group create --name "cli_test_group"

expect_succ pulp group permission add --groupname "cli_test_group" --permission "core.view_task"
expect_succ pulp group permission add --groupname "cli_test_group" --permission "auth.view_group"
expect_succ pulp group permission list --groupname "cli_test_group"
expect_succ pulp group permission remove --groupname "cli_test_group" --permission "core.view_task"

expect_succ pulp file repository create --name "cli_group_test_repository"
REPO_HREF="$(echo "$OUTPUT" | jq -r '.pulp_href')"
expect_succ pulp group permission -t object add --groupname "cli_test_group" --permission "file.view_filerepository" --object "$REPO_HREF"
expect_succ pulp group permission -t object list --groupname "cli_test_group"
expect_succ pulp group permission -t object remove --groupname "cli_test_group" --permission "file.view_filerepository" --object "$REPO_HREF"
