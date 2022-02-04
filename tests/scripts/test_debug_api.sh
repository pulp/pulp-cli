#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")"/config.source

expect_succ pulp -v status

echo "${ERROUTPUT}" | grep -q "^get https\?://\w.*${PULP_API_ROOT}api/v3/status/$"
