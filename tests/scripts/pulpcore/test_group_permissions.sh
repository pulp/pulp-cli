#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "core" --specifier "<3.20-dev" || exit 23

cleanup() {
  pulp group destroy --name "cli_test_group_permissions" || true
  pulp file repository destroy --name "cli_group_test_repository" || true
}
trap cleanup EXIT

expect_succ pulp group create --name "cli_test_group_permissions"

expect_succ pulp group permission add --group "cli_test_group_permissions" --permission "core.view_task"
expect_succ pulp group permission add --group "cli_test_group_permissions" --permission "auth.view_group"
expect_succ pulp group permission list --group "cli_test_group_permissions"
expect_succ pulp group permission remove --group "cli_test_group_permissions" --permission "core.view_task"

expect_succ pulp file repository create --name "cli_group_test_repository"
REPO_HREF="$(echo "$OUTPUT" | jq -r '.pulp_href')"
expect_succ pulp group permission -t object add --group "cli_test_group_permissions" --permission "file.view_filerepository" --object "$REPO_HREF"
expect_succ pulp group permission -t object list --group "cli_test_group_permissions"
expect_succ pulp group permission -t object remove --group "cli_test_group_permissions" --permission "file.view_filerepository" --object "$REPO_HREF"
