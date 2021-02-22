#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

expect_succ pulp worker list
href=$(echo "$OUTPUT" | jq -r ".[0].pulp_href")
expect_succ pulp worker show --href "$href"

expect_succ pulp worker list --missing
expect_succ pulp worker list --not-missing
expect_succ pulp worker list --online
expect_succ pulp worker list --not-online
expect_succ pulp worker list --name "resource-manager"

if pulp debug has-plugin --name "core" --min-version "3.10.0"
then
  expect_succ pulp worker list --name-contains "resource"
fi
