#!/bin/bash

set -eu
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
expect_succ pulp worker list --name-contains "resource"
