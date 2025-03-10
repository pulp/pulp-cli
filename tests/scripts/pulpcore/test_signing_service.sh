#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "core" || exit 23
pulp debug has-plugin --name "deb" || exit 23

expect_succ pulp signing-service list
expect_succ test "$(echo "$OUTPUT" | jq -r length)" -ge "1"
expect_succ pulp signing-service show --name "sign_deb_release"
