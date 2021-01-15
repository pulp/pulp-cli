#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")/config.source"

cleanup() {
  pulp rpm remote destroy --name "cli_test_rpm_remote" || true
  pulp rpm repository --name "cli_test_rpm_repository" destroy || true
  pulp rpm distribution destroy --name "cli_test_rpm_distro" || true
}
trap cleanup EXIT

if [ "$VERIFY_SSL" = "false" ]
then
  curl_opt="-k"
else
  curl_opt=""
fi

expect_succ pulp rpm remote create --name "cli_test_rpm_remote" --url "$RPM_REMOTE_URL"
expect_succ pulp rpm repository --name "cli_test_rpm_repository" create --remote "cli_test_rpm_remote"
expect_succ pulp rpm repository --name "cli_test_rpm_repository" sync
expect_succ pulp rpm publication create --repository "cli_test_rpm_repository"
PUBLICATION_HREF=$(echo "$OUTPUT" | jq -r .pulp_href)

expect_succ pulp rpm distribution create --name "cli_test_rpm_distro" \
  --base-path "cli_test_rpm_distro" \
  --publication "$PUBLICATION_HREF"

expect_succ curl "$curl_opt" --head --fail "$PULP_BASE_URL/pulp/content/cli_test_rpm_distro/config.repo"

expect_succ pulp rpm repository --name "cli_test_rpm_repository" version list
expect_succ pulp rpm repository --name "cli_test_rpm_repository" version repair --version 1

expect_succ pulp rpm distribution destroy --name "cli_test_rpm_distro"
expect_succ pulp rpm publication destroy --href "$PUBLICATION_HREF"
expect_succ pulp rpm repository --name "cli_test_rpm_repository" destroy
expect_succ pulp rpm remote destroy --name "cli_test_rpm_remote"
