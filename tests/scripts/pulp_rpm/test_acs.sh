#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "rpm" --specifier ">=3.18.0" || exit 23

# This container seems to have issues with the compression format of the fixture.
pulp debug has-plugin --name "rpm" --specifier "==3.20.0" && pulp debug has-plugin --name "core" --specifier "==3.23.21" && exit 23

acs_remote="cli_test_rpm_acs_remote"
acs="cli_test_rpm_acs"

cleanup() {
  pulp rpm repository destroy --name "cli-rpm-acs-repo-metadata-only" || true
  pulp rpm acs destroy --name $acs || true
  pulp rpm remote destroy --name $acs_remote || true
  pulp rpm remote destroy --name "cli-rpm-acs-remote-metadata-only" || true
}
trap cleanup EXIT

cleanup

expect_succ pulp rpm remote create --name $acs_remote --url "$PULP_FIXTURES_URL" --policy "on_demand"

expect_succ pulp rpm acs create --name $acs --remote $acs_remote --path "rpm-unsigned/" --path "rpm-signed/"
HREF="$(echo "$OUTPUT" | jq -r '.pulp_href')"
expect_succ pulp rpm acs list
test "$(echo "$OUTPUT" | jq -r length)" -ge 1
expect_succ pulp rpm acs show --acs "$HREF"
test "$(echo "$OUTPUT" | jq ".paths | length")" -eq 2

# manipulate paths
expect_succ pulp rpm acs path add --acs $acs --path "rpm-invalid/"
expect_succ pulp rpm acs show --acs $acs
test "$(echo "$OUTPUT" | jq ".paths | length")" -eq 3
expect_succ pulp rpm acs path remove --name $acs --path "rpm-invalid/"
expect_succ pulp rpm acs show --name $acs
test "$(echo "$OUTPUT" | jq ".paths | length")" -eq 2

# test refresh
expect_succ pulp rpm acs refresh --acs $acs
task_group=$(echo "$ERROUTPUT" | grep -E -o "/.*/api/v3/task-groups/[-[:xdigit:]]*/")
expect_succ pulp task-group show --href "$task_group"
test "$(echo "$OUTPUT" | jq ".tasks | length")" -eq 2

# create a remote with metadata only and sync it
expect_succ pulp rpm remote create --name "cli-rpm-acs-remote-metadata-only" --url "$PULP_FIXTURES_URL/rpm-unsigned-meta-only/"
remote_href="$(echo "$OUTPUT" | jq -r '.pulp_href')"
expect_succ pulp rpm repository create --name "cli-rpm-acs-repo-metadata-only" --remote "$remote_href"
expect_succ pulp rpm repository sync --repository "cli-rpm-acs-repo-metadata-only"

# test refresh with bad paths
expect_succ pulp rpm acs path add --acs $acs --path "bad-path/"
expect_fail pulp rpm acs refresh --acs $acs

expect_succ pulp rpm acs destroy --acs $acs
