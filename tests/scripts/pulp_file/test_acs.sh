#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "file" --specifier ">=1.10.0" || exit 23

acs_remote="cli_test_file_acs_remote"
acs="cli_test_acs"

cleanup() {
  pulp file acs destroy --name $acs || true
  pulp file repository destroy --name "cli-file-repo-manifest-only" || true
  pulp file remote destroy --name $acs_remote || true
  pulp file remote destroy --name "cli-file-remote-manifest-only" || true
}
trap cleanup EXIT

cleanup

expect_succ pulp file remote create --name $acs_remote --url "$PULP_FIXTURES_URL" --policy "on_demand"

expect_succ pulp file acs create --name $acs --remote $acs_remote --path "file/PULP_MANIFEST" --path "file2/PULP_MANIFEST"
HREF="$(echo "$OUTPUT" | jq -r '.pulp_href')"

expect_succ pulp file acs list
test "$(echo "$OUTPUT" | jq -r length)" -ge 1
expect_succ pulp file acs show --name $acs
test "$(echo "$OUTPUT" | jq ".paths | length")" -eq 2

# manipulate paths
expect_succ pulp file acs path add --acs "$HREF" --path "file-invalid/PULP_MANIFEST"
expect_succ pulp file acs show --acs $acs
test "$(echo "$OUTPUT" | jq ".paths | length")" -eq 3
expect_succ pulp file acs path remove --acs $acs --path "file-invalid/PULP_MANIFEST"
expect_succ pulp file acs show --name $acs
test "$(echo "$OUTPUT" | jq ".paths | length")" -eq 2

# test refresh
expect_succ pulp --background file acs refresh --acs $acs
task_group=$(echo "$ERROUTPUT" | grep -E -o "/.*/api/v3/task-groups/[-[:xdigit:]]*/")
expect_succ pulp task-group show --href "$task_group" --wait

group_task_uuid="${task_group%/}"
group_task_uuid="${group_task_uuid##*/}"
expect_succ pulp task-group show --uuid "$group_task_uuid"

test "$(echo "$OUTPUT" | jq ".tasks | length")" -eq 2

# create a remote with manifest only and sync it
expect_succ pulp file remote create --name "cli-file-remote-manifest-only" --url "$PULP_FIXTURES_URL/file-manifest/PULP_MANIFEST"
remote_href="$(echo "$OUTPUT" | jq -r '.pulp_href')"
expect_succ pulp file repository create --name "cli-file-repo-manifest-only" --remote "$remote_href"
expect_succ pulp file repository sync --repository "cli-file-repo-manifest-only"

# test refresh with bad paths
expect_succ pulp file acs path add --name $acs --path "bad-path/PULP_MANIFEST"
expect_fail pulp file acs refresh --acs $acs

expect_succ pulp file acs destroy --name $acs
