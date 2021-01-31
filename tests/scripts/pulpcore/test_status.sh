#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

expect_succ pulp status

test "$(echo "${OUTPUT}" | jq -r '.database_connection.connected' )" = "true"
