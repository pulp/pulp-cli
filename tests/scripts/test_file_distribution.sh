#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")/config.source"

cleanup() {
  pulp file remote destroy --name "cli_test_file_remote" || true
  pulp file repository destroy --name "cli_test_file_repository" || true
  pulp file distribution destroy --name "cli_test_file_distro" || true
}
trap cleanup EXIT

if [ "$VERIFY_SSL" = "false" ]
then
  curl_opt="-k"
else
  curl_opt=""
fi

expect_succ pulp file remote create --name "cli_test_file_remote" --url "$FILE_REMOTE_URL"
expect_succ pulp file repository create --name "cli_test_file_repository" --remote "cli_test_file_remote"
expect_succ pulp file repository sync --name "cli_test_file_repository"
expect_succ pulp file publication create --repository "cli_test_file_repository"
PUBLICATION_HREF=$(echo "$OUTPUT" | jq -r .pulp_href)

expect_succ pulp file distribution create --name "cli_test_file_distro" --base-path "wrong_path" 
expect_succ pulp file distribution update \
  --name "cli_test_file_distro" \
  --base-path "cli_test_file_distro" \
  --publication "$PUBLICATION_HREF"

expect_succ curl "$curl_opt" --head --fail "$PULP_BASE_URL/pulp/content/cli_test_file_distro/1.iso"

expect_succ pulp file distribution destroy --name "cli_test_file_distro"
