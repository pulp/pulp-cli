#!/bin/sh

set -euv

PULP_CLI=pulp
BASE_URL="http://pulp3-sandbox-debian10"
USER="admin"
PASSWORD="password"

STATUS_RESULT=$($PULP_CLI --base-url "${BASE_URL}" --user "${USER}" --password "${PASSWORD}" status)

test "$(echo "${STATUS_RESULT}" | jq '.database_connection.connected' )" = "true"
