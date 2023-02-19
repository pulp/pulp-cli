#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "rpm" || exit 23

cleanup() {
  pulp rpm remote destroy --name "cli_test_rpm_remote" || true
}
trap cleanup EXIT

expect_succ pulp rpm remote list

expect_succ pulp rpm remote create --name "cli_test_rpm_remote" --url "$RPM_REMOTE_URL" --proxy-url "http://proxy.org" --proxy-username "user" --proxy-password "pass"
HREF="$(echo "$OUTPUT" | jq -r '.pulp_href')"
expect_succ pulp rpm remote show --remote "$HREF"
expect_succ pulp rpm remote list
expect_succ pulp rpm remote update --remote "cli_test_rpm_remote" --sles-auth-token "0123456789abcdef"
expect_succ pulp rpm remote destroy --remote "cli_test_rpm_remote"
