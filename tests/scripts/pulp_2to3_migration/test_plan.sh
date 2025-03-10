#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "pulp_2to3_migration" || exit 23

plan_href=""
PLANFILE="$(dirname "$(realpath "$0")")"/plan.json
plan_json=$(cat "$PLANFILE")

cleanup() {
  pulp migration plan destroy --href "$plan_href" || true
}
trap cleanup EXIT

#Test create with plan-string
expect_succ pulp migration plan create --plan "$plan_json"
plan_href=$(echo "$OUTPUT" | jq -r '.pulp_href')
expect_succ pulp migration plan show --href "$plan_href"

expect_succ pulp migration plan list
expect_succ pulp migration plan destroy --href "$plan_href"

#Test create with plan-file
expect_succ pulp migration plan create --plan @"$PLANFILE"
plan_href=$(echo "$OUTPUT" | jq -r '.pulp_href')
expect_succ pulp migration plan show --href "$plan_href"
expect_succ pulp migration plan destroy --href "$plan_href"
