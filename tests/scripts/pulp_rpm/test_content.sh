#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "rpm" || exit 3

cleanup() {
  pulp rpm repository destroy --name "cli_test_rpm_repository" || true
  pulp rpm remote destroy --name "cli_test_rpm_remote" || true
}
trap cleanup EXIT

# Test rpm package upload

wget "https://fixtures.pulpproject.org/rpm-unsigned/bear-4.1-1.noarch.rpm"
expect_succ pulp rpm content upload --file "bear-4.1-1.noarch.rpm" --relative-path "bear-4.1-1.noarch.rpm"
PACKAGE_HREF=$(echo "$OUTPUT" | jq -r .pulp_href)
expect_succ pulp rpm content show --href "$PACKAGE_HREF"

expect_succ pulp rpm remote create --name "cli_test_rpm_remote" --url "$RPM_REMOTE_URL"
expect_succ pulp rpm remote show --name "cli_test_rpm_remote"
REMOTE_HREF=$(echo "$OUTPUT" | jq -r .pulp_href)
expect_succ pulp rpm repository create --name "cli_test_rpm_repository" --remote "$REMOTE_HREF"
expect_succ pulp rpm repository show --name "cli_test_rpm_repository"

expect_succ pulp rpm repository content modify \
--repository "cli_test_rpm_repository" \
--add-content "[{\"pulp_href\": \"$PACKAGE_HREF\"}]"
expect_succ pulp rpm repository content list --repository "cli_test_rpm_repository"
test "$(echo "$OUTPUT" | jq -r '.[0].pulp_href')" = "$PACKAGE_HREF"

expect_succ pulp rpm repository content modify \
--repository "cli_test_rpm_repository" \
--remove-content "[{\"pulp_href\": \"$PACKAGE_HREF\"}]"
expect_succ pulp rpm repository content list --repository "cli_test_rpm_repository"
test "$(echo "$OUTPUT" | jq -r length)" -eq "0"

expect_succ pulp rpm repository content add \
--repository "cli_test_rpm_repository" \
--package-href "$PACKAGE_HREF"
expect_succ pulp rpm repository content list --repository "cli_test_rpm_repository"
test "$(echo "$OUTPUT" | jq -r '.[0].pulp_href')" = "$PACKAGE_HREF"

expect_succ pulp rpm repository content remove \
--repository "cli_test_rpm_repository" \
--package-href "$PACKAGE_HREF"
expect_succ pulp rpm repository content list --repository "cli_test_rpm_repository"
test "$(echo "$OUTPUT" | jq -r length)" -eq "0"

expect_succ pulp rpm repository content modify \
--repository "cli_test_rpm_repository" \
--remove-content "[{\"pulp_href\": \"$PACKAGE_HREF\"}]"
expect_succ pulp rpm repository destroy --name "cli_test_rpm_repository"
expect_succ pulp rpm remote destroy --name "cli_test_rpm_remote"
