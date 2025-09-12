#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "rpm" --specifier ">=3.27.0.dev" || exit 23

cleanup() {
  pulp rpm repository destroy --name "cli_test_rpm_prune" || true
  pulp rpm repository destroy --name "cli_test_rpm_prune_2" || true
  pulp rpm remote destroy --name "cli_test_rpm_prune" || true
}
trap cleanup EXIT

expect_succ pulp rpm remote create --name "cli_test_rpm_prune" --url "$RPM_REMOTE_URL" --policy on_demand
expect_succ pulp rpm repository create --name "cli_test_rpm_prune" --remote "cli_test_rpm_prune" --no-autopublish
repo_href="$(echo "$OUTPUT" | jq -r '.pulp_href')"
expect_succ pulp rpm repository create --name "cli_test_rpm_prune_2" --remote "cli_test_rpm_prune" --no-autopublish
repo_href_2="$(echo "$OUTPUT" | jq -r '.pulp_href')"
expect_succ pulp rpm repository sync --repository "cli_test_rpm_prune"
expect_succ pulp rpm repository sync --repository "cli_test_rpm_prune_2"

expect_fail pulp rpm prune-packages
expect_fail pulp rpm prune-packages --repository "rpm:rpm:cli_test_rpm_prune" --all-repositories
expect_fail pulp rpm prune-packages --repository "rpm:rpm:cli_test_rpm_prune" --keep-days foo
expect_fail pulp rpm prune-packages --repository "rpm:rpm:cli_test_rpm_prune" --concurrency bar

expect_succ pulp rpm prune-packages --repository "rpm:rpm:cli_test_rpm_prune" --keep-days 0 --dry-run
expect_succ pulp rpm prune-packages --repository "${repo_href}" --keep-days 0 --dry-run
expect_succ pulp rpm prune-packages --repository "${repo_href}" --repository "${repo_href_2}" --dry-run
expect_succ pulp rpm prune-packages --repository "rpm:rpm:cli_test_rpm_prune" --repository "rpm:rpm:cli_test_rpm_prune_2" --dry-run
expect_succ pulp rpm prune-packages --repository "rpm:rpm:cli_test_rpm_prune" --repository "${repo_href}" --repository "${repo_href_2}" --dry-run
# This task can fail in parallel tests, so run in background. We only care that the task is created
expect_succ pulp -b rpm prune-packages --all-repositories --dry-run
expect_succ pulp rpm prune-packages --repository "rpm:rpm:cli_test_rpm_prune" --keep-days 0
