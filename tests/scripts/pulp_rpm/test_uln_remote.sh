#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "rpm" --min-version "3.12.0" || exit 3

# Set USERNAME, USERPASS, and ULN_REMOTE_URL for tests to work.

USERNAME="user"
USERPASS="changeme"

cleanup() {
  pulp rpm remote --type uln destroy --name "cli_test_uln_remote" || true
}
trap cleanup EXIT

expect_succ pulp rpm remote --type uln list

expect_succ pulp rpm remote --type uln create --name "cli_test_uln_remote" --url "$ULN_REMOTE_URL" --username "$USERNAME" --password "$USERPASS"
expect_succ pulp rpm remote --type uln show --name "cli_test_uln_remote"
expect_succ pulp rpm remote --type uln list
expect_succ pulp rpm remote --type uln update --name "cli_test_uln_remote" --uln-server-base-url "https://linux.com/"
expect_succ pulp rpm remote --type uln destroy --name "cli_test_uln_remote"
