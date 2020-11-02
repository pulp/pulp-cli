#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")/config.source"

cleanup() {
  pulp file remote destroy --name "cli_test_file_remote" || true
  pulp file repository destroy --name "cli_test_file_repository" || true
}
trap cleanup EXIT

pulp file remote create --name "cli_test_file_remote" --url "$FILE_REMOTE_URL"
pulp file repository create --name "cli_test_file_repository" --remote "cli_test_file_remote"
pulp file repository sync --name "cli_test_file_repository"

expect_succ pulp file publication create --repository "cli_test_file_repository"
PUBLICATION_HREF="$(echo "$OUTPUT" | jq -r .pulp_href)"
expect_succ pulp file publication destroy --href "$PUBLICATION_HREF"
