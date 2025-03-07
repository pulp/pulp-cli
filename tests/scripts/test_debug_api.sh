#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")"/config.source

expect_succ pulp -v status
echo "${ERROUTPUT}" | grep -q "^status_read : get https\?://\w.*/api/v3/status/$"

expect_succ pulp -vv --header "test-header:Value with space" status
echo "${ERROUTPUT}" | grep -q "^  test-header: Value with space$"
