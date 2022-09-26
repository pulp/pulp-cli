#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

cleanup() {
  pulp file repository destroy --name aaaaaaaaaa || true
  pulp file repository destroy --name bbbbbbbbbb || true
  pulp file repository destroy --name cccccccccc || true
}
trap cleanup EXIT

expect_succ pulp file repository create --name aaaaaaaaaa
expect_succ pulp file repository create --name bbbbbbbbbb
expect_succ pulp file repository create --name cccccccccc

expect_succ pulp file repository list --ordering -name
ORDERED_RESULTS=$(echo "$OUTPUT" | jq -r .[].name | tr "\n" " " | xargs)
EXPECTED_RESULTS="cccccccccc bbbbbbbbbb aaaaaaaaaa"
if [[ "$ORDERED_RESULTS" != "$EXPECTED_RESULTS" ]]; then
  echo "Ordered results do not match: {$ORDERED_RESULTS} != {$EXPECTED_RESULTS}"
  exit 1
fi

expect_succ pulp file repository list --field name --field remote
SELECTED_FIELDS=$(echo "$OUTPUT" | jq -r ".[] | keys[]" | sort| tr "\n" " " | xargs)
EXPECTED_FIELDS="name name name remote remote remote"
if [[ "$SELECTED_FIELDS" != "$EXPECTED_FIELDS" ]]; then
  echo "Selected fields do not match: {$SELECTED_FIELDS} != {$EXPECTED_FIELDS}"
  exit 1
fi

expect_succ pulp file repository list --exclude-field name --exclude-field remote
EXCLUDED_FIELDS=$(echo "$OUTPUT" | jq -r ".[] | keys[]" | tr "\n" " " )

if [[ "$EXCLUDED_FIELDS" == *"name"* ]]; then
  echo "The name field was not excluded from {$EXCLUDED_FIELDS}"
  exit 1
fi
if [[ "$EXCLUDED_FIELDS" == *"remote"* ]]; then
  echo "The remote field was not excluded from {$EXCLUDED_FIELDS}"
  exit 1
fi
