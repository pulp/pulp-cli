#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "container" || exit 3

cleanup() {
  pulp container repository destroy --name "cli_test_source_container_repository" || true
  pulp container repository destroy --name "cli_test_dest_container_repository" || true
  pulp container remote destroy --name "cli_test_container_remote" || true
  pulp orphan cleanup || true
}
trap cleanup EXIT

# Prepare
pulp container remote create --name "cli_test_container_remote" --url "$CONTAINER_REMOTE_URL" --upstream-name "$CONTAINER_IMAGE"
source_href="$(pulp container repository create --name "cli_test_source_container_repository" | jq -r .pulp_href)"
pulp container repository create --name "cli_test_dest_container_repository"
HREF="$(echo "$OUTPUT" | jq -r "pulp_href")"

pulp container repository sync --repository "cli_test_source_container_repository" --remote "cli_test_container_remote"
tag="$(pulp container repository content -t 'tag' list --repository "cli_test_source_container_repository" | jq -r .[0].name)"
digest="$(pulp container repository content -t 'manifest' list --repository "cli_test_source_container_repository" | jq -r '.[] | select(.listed_manifests == []) | .digest' | sed -n '1p')"

# Test copying manifests
expect_succ pulp container repository copy-manifest --repository "cli_test_dest_container_repository" --source "cli_test_source_container_repository" --digest "$digest"
expect_succ pulp container repository content -t 'manifest' list --repository "cli_test_dest_container_repository"
test "$(echo "$OUTPUT" | jq -r length)" -eq 1
test "$(echo "$OUTPUT" | jq -r .[0].digest)" = "$digest"

expect_succ pulp container repository copy-manifest --repository "cli_test_dest_container_repository" --source "cli_test_source_container_repository" --version "1" --media-type "application/vnd.docker.distribution.manifest.v2+json"
expect_succ pulp container repository content -t 'manifest' list --repository "cli_test_dest_container_repository" --version "2"
copied="$(echo "$OUTPUT" | jq -r length)"
test "$copied" -gt 1

expect_succ pulp container repository copy-manifest --repository "$HREF" --source "$source_href"
expect_succ pulp container repository content -t 'manifest' list --repository "cli_test_dest_container_repository" --version "3"
test "$(echo "$OUTPUT" | jq -r length)" -gt "$copied"

# Test copying tags
expect_succ pulp container repository copy-tag --repository "$HREF" --source "cli_test_source_container_repository" --tag "$tag"
expect_succ pulp container repository content -t 'tag' list --repository "cli_test_dest_container_repository" --version "4"
test "$(echo "$OUTPUT" | jq -r length)" -eq 1
test "$(echo "$OUTPUT" | jq -r .[0].name)" = "$tag"

expect_succ pulp container repository copy-tag --repository "cli_test_dest_container_repository" --source "$source_href" --version "1"
expect_succ pulp container repository content -t 'tag' list --repository "cli_test_dest_container_repository" --version "5"
test "$(echo "$OUTPUT" | jq -r length)" -gt 1

# Test bad versions
expect_fail pulp container repository copy-tag --name "cli_test_source_container_repository" --source "cli_test_dest_container_repository" --version "0"
expect_fail pulp container repository copy-manifest --name "cli_test_source_container_repository" --source "cli_test_dest_container_repository" --version "6"
test "$ERROUTPUT" = "Error: Please specify a version that between 0 and the latest version 5"
