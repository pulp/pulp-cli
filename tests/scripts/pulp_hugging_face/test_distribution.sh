#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "hugging_face" || exit 23

cleanup() {
  pulp hugging-face distribution destroy --name "cli_test_hugging_face_distro" || true
  pulp hugging-face repository destroy --name "cli_test_hugging_face_distro_repo" || true
  pulp hugging-face remote destroy --name "cli_test_hugging_face_distro_remote" || true
}
trap cleanup EXIT

REMOTE_HREF="$(pulp hugging-face remote create --name "cli_test_hugging_face_distro_remote" --url "https://huggingface.co/" --policy "on_demand" | jq -r '.pulp_href')"
REPO_HREF="$(pulp hugging-face repository create --name "cli_test_hugging_face_distro_repo" | jq -r '.pulp_href')"

expect_succ pulp hugging-face distribution create --name "cli_test_hugging_face_distro" --base-path "cli_test_hugging_face_distro" --remote "cli_test_hugging_face_distro_remote"
expect_succ pulp hugging-face distribution show --distribution "cli_test_hugging_face_distro"
test "$(echo "$OUTPUT" | jq -r '.remote')" = "$REMOTE_HREF"

expect_succ pulp hugging-face distribution update --distribution "cli_test_hugging_face_distro" --remote "" --repository "cli_test_hugging_face_distro_repo"
expect_succ pulp hugging-face distribution show --distribution "cli_test_hugging_face_distro"
test "$(echo "$OUTPUT" | jq -r '.remote')" = "null"
test "$(echo "$OUTPUT" | jq -r '.repository')" = "$REPO_HREF"

expect_succ pulp hugging-face distribution update --distribution "cli_test_hugging_face_distro" --repository ""
expect_succ pulp hugging-face distribution show --distribution "cli_test_hugging_face_distro"
test "$(echo "$OUTPUT" | jq -r '.repository')" = "null"

expect_succ pulp hugging-face distribution list --base-path "cli_test_hugging_face_distro"
test "$(echo "$OUTPUT" | jq -r length)" -eq 1

expect_succ pulp hugging-face distribution destroy --distribution "cli_test_hugging_face_distro"
