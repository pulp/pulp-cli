#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "file" || exit 23

cleanup() {
  pulp file repository destroy --name query_params_aaaaaaaaaa || true
  pulp file repository destroy --name query_params_bbbbbbbbbb || true
  pulp file repository destroy --name query_params_cccccccccc || true
}
trap cleanup EXIT

expect_succ pulp file repository create --name query_params_aaaaaaaaaa
expect_succ pulp file repository create --name query_params_bbbbbbbbbb
expect_succ pulp file repository create --name query_params_cccccccccc

expect_succ pulp file repository list --ordering -name --name-startswith query_params
if ! (echo "$OUTPUT" | jq -r .[].name | sort -r -C -); then
  echo -e "Ordered results are not in a reverse alphabetical order.\n$(echo "$OUTPUT" | jq -r .[].name)"
  exit 1
fi

expect_succ pulp file repository list --ordering name --name-startswith query_params
if ! (echo "$OUTPUT" | jq -r .[].name | sort -C -); then
  echo -e "Ordered results are not in an alphabetical order.\n$(echo "$OUTPUT" | jq -r .[].name)"
  exit 1
fi

expect_succ pulp file repository list --field name --field remote --name-startswith query_params
SELECTED_FIELDS=$(echo "$OUTPUT" | jq -r ".[] | keys[]" | sort -u | tr "\n" " " | xargs)
EXPECTED_FIELDS="name remote"
if [[ "$SELECTED_FIELDS" != "$EXPECTED_FIELDS" ]]; then
  echo "Selected fields do not match: {$SELECTED_FIELDS} != {$EXPECTED_FIELDS}"
  exit 1
fi

expect_succ pulp file repository list --exclude-field name --exclude-field remote --name-startswith query_params
EXCLUDED_FIELDS=$(echo "$OUTPUT" | jq -r ".[] | keys[]" | tr "\n" " " )

if [[ "$EXCLUDED_FIELDS" == *"name"* ]]; then
  echo "The name field was not excluded from {$EXCLUDED_FIELDS}"
  exit 1
fi
if [[ "$EXCLUDED_FIELDS" == *"remote"* ]]; then
  echo "The remote field was not excluded from {$EXCLUDED_FIELDS}"
  exit 1
fi
