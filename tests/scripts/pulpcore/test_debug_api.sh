#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

expect_succ pulp -v status

echo "${ERROUTPUT}" | grep -q "^get https\?://\w.*/pulp/api/v3/status/$"
