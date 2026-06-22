#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "hugging_face" || exit 23

cleanup() {
  pulp hugging-face repository destroy --name "cli_test_hugging_face_repo" || true
}
trap cleanup EXIT

expect_succ pulp hugging-face repository list

expect_succ pulp hugging-face repository create --name "cli_test_hugging_face_repo" --description "Test repository for CLI tests"
HREF="$(echo "$OUTPUT" | jq -r '.pulp_href')"
expect_succ pulp hugging-face repository update --repository "cli_test_hugging_face_repo" --description ""
expect_succ pulp hugging-face repository show --repository "$HREF"
test "$(echo "$OUTPUT" | jq -r '.description')" = "null"

expect_succ pulp hugging-face repository update --repository "cli_test_hugging_face_repo" --description $'Test\nrepository'
expect_succ pulp hugging-face repository show --repository "cli_test_hugging_face_repo"
test "$(echo "$OUTPUT" | jq '.description')" = '"Test\nrepository"'

expect_succ pulp hugging-face repository version list --repository "cli_test_hugging_face_repo"
test "$(echo "$OUTPUT" | jq -r '.|length')" = "1"

expect_succ pulp hugging-face repository list
test "$(echo "$OUTPUT" | jq -r '.|length')" != "0"
expect_succ pulp hugging-face repository list --name-contains "cli_test_hugging_face"
test "$(echo "$OUTPUT" | jq -r '.|length')" -ge "1"

expect_succ pulp hugging-face repository destroy --repository "cli_test_hugging_face_repo"