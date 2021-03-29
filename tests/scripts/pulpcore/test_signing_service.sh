#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "core" --min-version 3.11 || exit 3
pulp debug has-plugin --name "deb" || exit 3

expect_succ pulp signing-service list
expect_succ test "$(echo "$OUTPUT" | jq -r length)" -ge "1"
expect_succ pulp signing-service show --name "sign_deb_release"
