#!/bin/sh

. "$(dirname "$(realpath "$0")")/config.source"

STATUS_RESULT=$(pulp_cli orphans delete)

test "$(echo "${STATUS_RESULT}" | jq -r '.state' )" = "completed"
