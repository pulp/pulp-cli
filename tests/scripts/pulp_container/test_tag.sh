#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "container" || exit 3

cleanup() {
  pulp container repository destroy --name "cli_test_container_repository" || true
  pulp container remote destroy --name "cli_test_container_remote" || true
  pulp orphan cleanup || true
}
trap cleanup EXIT

# Prepare
pulp container remote create --name "cli_test_container_remote" --url "$CONTAINER_REMOTE_URL" --upstream-name "$CONTAINER_IMAGE"
pulp container repository create --name "cli_test_container_repository"
pulp container repository sync --repository "cli_test_container_repository" --remote "cli_test_container_remote"
manifest_digest="$(pulp container content -t manifest list | tr '\r\n' ' ' | jq -r .[0].digest)"

expect_succ pulp container repository tag --repository "cli_test_container_repository" --tag "test_tag" --digest "$manifest_digest"
expect_succ pulp container repository version show --repository "cli_test_container_repository" --version "2"
test "$(echo "$OUTPUT" | jq -r '.content_summary.added["container.tag"].count')" -eq "1"

expect_succ pulp container repository untag --repository "cli_test_container_repository" --tag "test_tag"
expect_succ pulp container repository version show --repository "cli_test_container_repository" --version "3"
test "$(echo "$OUTPUT" | jq -r '.content_summary.removed["container.tag"].count')" -eq "1"
