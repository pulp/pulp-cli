#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "core" --specifier ">=3.19.0" || exit 23
pulp debug has-plugin --name "file" || exit 23

cleanup() {
  pulp file repository destroy --name "cli_test_reclaim_repo" || true
  pulp file remote destroy --name "cli_test_reclaim_remote" || true
  pulp file distribution destroy --name "cli_test_reclaim_distro" || true
}
trap cleanup EXIT

# Setup needed prerequisites
expect_succ pulp file remote create --name "cli_test_reclaim_remote" --url "$FILE_REMOTE2_URL" --policy immediate
expect_succ pulp file repository create --name "cli_test_reclaim_repo" --remote "cli_test_reclaim_remote" --autopublish
expect_succ pulp file repository sync --name "cli_test_reclaim_repo"
expect_succ pulp file distribution create --name "cli_test_reclaim_distro" --base-path "cli_test_reclaim_distro" --repository "cli_test_reclaim_repo"

# Verify that the artifact was created
expect_succ pulp file repository content list --repository "cli_test_reclaim_repo" --version 1
ARTIFACT="$(echo "$OUTPUT" | jq -r '.[] | select(.relative_path | endswith("1.iso")) | .artifact')"
test "$ARTIFACT" != "null"

# Reclaim disk space with repo version 1 on keeplist and verify that the artifact wasn't affected
expect_succ pulp repository reclaim --repository "file:file:cli_test_reclaim_repo" --keep-version "file:file:cli_test_reclaim_repo" 1
expect_succ pulp file repository content list --repository "cli_test_reclaim_repo" --version 1
test "$(echo "$OUTPUT" | jq -r '.[] | select(.relative_path | endswith("1.iso")) | .artifact')" = "$ARTIFACT"

# Reclaim disk space and verify that the artifact is no longer available
expect_succ pulp repository reclaim --repository "file:file:cli_test_reclaim_repo"
expect_succ pulp file repository content list --repository "cli_test_reclaim_repo" --version 1
test "$(echo "$OUTPUT" | jq -r '.[] | select(.relative_path | endswith("1.iso")) | .artifact')" = "null"
