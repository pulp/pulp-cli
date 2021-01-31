#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

expect_succ pulp orphans delete

test "$(echo "${OUTPUT}" | jq -r '.state' )" = "completed"
