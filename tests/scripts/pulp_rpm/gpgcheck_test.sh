#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "rpm" --max-version "3.23.0" || exit 23

cleanup () {
  pulp rpm repository destroy --name "cli-repo-gpgcheck" || true
}
trap cleanup EXIT

if pulp debug has-plugin --name "rpm" --specifier "<=3.29.0"
then
  expect succ pulp rpm repository create --name "cli-repo-gpgcheck" --gpgcheck 1 --repo-gpgcheck 1
  expect succ pulp rpm repository show --name "cli-repo-gpgcheck"
  test "$(echo "$OUTPUT" | jq -r '.gpgcheck')" = 1
  test "$(echo "$OUTPUT" | jq -r '.repo_gpgcheck')" = 1

  expect succ pulp rpm repository update --name "cli-repo-gpgcheck" --gpgcheck 0 --repo-gpgcheck 0
  expect succ pulp rpm repository show --name "cli-repo-gpgcheck"
  test "$(echo "$OUTPUT" | jq -r '.gpgcheck')" = 0
  test "$(echo "$OUTPUT" | jq -r '.repo_gpgcheck')" = 0
else
  expect fail pulp rpm repository create --name "cli-repo-gpgcheck" --gpgcheck 1
  expect fail pulp rpm repository create --name "cli-repo-gpgcheck" --repo-gpgcheck 1
fi

if pulp debug has-plugin --name "rpm" --specifier ">=3.24.0"
then
  expect succ pulp rpm repository create --name "cli-repo-config" --repo-config "{\"gpgcheck\"=1, \"repo_gpgcheck\"=1}"
  expect succ pulp rpm repository show --name "cli-repo-config"
  test "$(echo "$OUTPUT" | jq -r '.gpgcheck')" = 1
  test "$(echo "$OUTPUT" | jq -r '.repo_gpgcheck')" = 1

  expect succ pulp rpm repository update --name "cli-repo-config" --repo-config "{\"gpgcheck\"=0, \"repo_gpgcheck\"=0}"
  expect succ pulp rpm repository show --name "cli-repo-config"
  test "$(echo "$OUTPUT" | jq -r '.gpgcheck')" = 0
  test "$(echo "$OUTPUT" | jq -r '.repo_gpgcheck')" = 0
fi