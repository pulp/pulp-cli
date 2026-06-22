#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "hugging_face" || exit 23

cleanup() {
  pulp hugging-face remote destroy --name "cli_test_hugging_face_remote" || true
}
trap cleanup EXIT

expect_succ pulp hugging-face remote list

expect_succ pulp hugging-face remote create --name "cli_test_hugging_face_remote" --url "https://huggingface.co/" --policy "on_demand" --hf-token "s3cr3t"
expect_succ pulp hugging-face remote show --remote "cli_test_hugging_face_remote"
HREF="$(echo "$OUTPUT" | jq -r '.pulp_href')"
test "$(echo "$OUTPUT" | jq -r '.policy')" = "on_demand"
# hf_token is write-only and must never be returned in API responses.
test "$(echo "$OUTPUT" | jq -r '.hf_token')" = "null"

expect_succ pulp hugging-face remote update --remote "$HREF" --policy "immediate"
expect_succ pulp hugging-face remote show --remote "cli_test_hugging_face_remote"
test "$(echo "$OUTPUT" | jq -r '.policy')" = "immediate"

expect_succ pulp hugging-face remote list --name-contains "li_test_hugging_face_remot"
test "$(echo "$OUTPUT" | jq -r '.|length')" = "1"

expect_succ pulp hugging-face remote destroy --remote "cli_test_hugging_face_remote"