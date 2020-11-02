#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")/config.source"

expect_succ pulp_cli orphans delete

test "$(echo "${OUTPUT}" | jq -r '.state' )" = "completed"
