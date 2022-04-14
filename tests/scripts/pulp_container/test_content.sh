#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "container" || exit 3

cleanup() {
  pulp container remote destroy --name "cli_test_container_remote" || true
  pulp container repository destroy --name "cli_test_container_repository" || true
  pulp orphan cleanup || true
}
trap cleanup EXIT

# Prepare
pulp container remote create --name "cli_test_container_remote" --url "$CONTAINER_REMOTE_URL" --upstream-name "$CONTAINER_IMAGE"
pulp container repository create --name "cli_test_container_repository"
pulp container repository sync --name "cli_test_container_repository" --remote "cli_test_container_remote"

# Check each content list
expect_succ pulp container content -t blob list
test "$(echo "$OUTPUT" | jq -r length)" -gt "0"
blob_href="$(echo "$OUTPUT" | tr '\r\n' ' ' | jq -r .[0].pulp_href)"
blob_digest="$(echo "$OUTPUT" | tr '\r\n' ' ' | jq -r .[0].digest)"

expect_succ pulp container content -t manifest list
test "$(echo "$OUTPUT" | jq -r length)" -gt "0"
manifest_href="$(echo "$OUTPUT" | tr '\r\n' ' ' | jq -r .[0].pulp_href)"
manifest_digest="$(echo "$OUTPUT" | tr '\r\n' ' ' | jq -r .[0].digest)"

expect_succ pulp container content -t tag list
test "$(echo "$OUTPUT" | jq -r length)" -gt "0"
tag_href="$(echo "$OUTPUT" | tr '\r\n' ' ' | jq -r .[0].pulp_href)"
tag_name="$(echo "$OUTPUT" | tr '\r\n' ' ' | jq -r .[0].name)"
tag_manifest="$(echo "$OUTPUT" | tr '\r\n' ' ' | jq -r .[0].tagged_manifest)"

expect_succ pulp container content -t blob show --digest "$blob_digest"
test "$(echo "$OUTPUT" | jq -r .pulp_href)" = "$blob_href"
expect_fail pulp container content -t blob show --digest "$manifest_digest"

expect_succ pulp container content -t manifest show --digest "$manifest_digest"
test "$(echo "$OUTPUT" | jq -r .pulp_href)" = "$manifest_href"
expect_succ pulp container content -t manifest show --href "$tag_manifest"
tag_digest="$(echo "$OUTPUT" | jq -r .digest)"

expect_succ pulp container content -t tag show --name "$tag_name" --digest "$tag_digest"
test "$(echo "$OUTPUT" | jq -r .pulp_href)" = "$tag_href"

# Test repository content commands
expect_succ pulp container repository content list --repository "cli_test_container_repository" --all-types
expect_succ pulp container repository content --type "tag" list --repository "cli_test_container_repository"
expect_succ pulp container repository content --type "manifest" list --repository "cli_test_container_repository"
expect_succ pulp container repository content --type "blob" list --repository "cli_test_container_repository"

expect_succ pulp container repository content --type "blob" remove --repository "cli_test_container_repository" --digest "$blob_digest"
expect_succ pulp container repository content --type "manifest" remove --repository "cli_test_container_repository" --digest "$manifest_digest"
expect_succ pulp container repository content --type "tag" remove --repository "cli_test_container_repository" --name "$tag_name" --digest "$tag_digest"

expect_succ pulp container repository content add --repository "cli_test_container_repository" --href "$blob_href"
expect_succ pulp container repository content add --repository "cli_test_container_repository" --href "$manifest_href"
expect_succ pulp container repository content add --repository "cli_test_container_repository" --href "$tag_href"
