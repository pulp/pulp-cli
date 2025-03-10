#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

expect_succ pulp status

test "$(echo "${OUTPUT}" | jq -r '.database_connection.connected' )" = "true"

expect_succ pulp -vv --cid deadbeefdeadbeefdeadbeefdeadbeef status

echo "${ERROUTPUT}" | grep -q "Correlation-ID: deadbeefdeadbeefdeadbeefdeadbeef"

expect_fail pulp --cid deadbeefdeadbeefdeadbeefdeadxxxx status
