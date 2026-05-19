#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "python" --specifier ">=3.30.2" || exit 23

cleanup() {
  pulp python repository destroy --name "cli_test_python_blocklist" || true
}
trap cleanup EXIT

expect_succ pulp python repository create --name "cli_test_python_blocklist"

# Test adding blocklist entries
expect_succ pulp python repository blocklist add --repository "cli_test_python_blocklist" --name "pkg"
test "$(echo "$OUTPUT" | jq -r '.name')" = "pkg"
test "$(echo "$OUTPUT" | jq -r '.version')" = "null"
test "$(echo "$OUTPUT" | jq -r '.filename')" = "null"
ENTRY_HREF="$(echo "$OUTPUT" | jq -r '.pulp_href')"
expect_succ pulp python repository blocklist add --repository "cli_test_python_blocklist" --name "pkg" --version "2.0"
expect_succ pulp python repository blocklist add --repository "cli_test_python_blocklist" --filename "pkg-3.0.tar.gz"

# Test listing blocklist entries
expect_succ pulp python repository blocklist list --repository "cli_test_python_blocklist"
expect_succ test "$(echo "$OUTPUT" | jq -r '.|length')" = "3"
expect_succ pulp python repository blocklist list --repository "cli_test_python_blocklist" --name "pkg"
expect_succ test "$(echo "$OUTPUT" | jq -r '.|length')" = "2"
expect_succ pulp python repository blocklist list --repository "cli_test_python_blocklist" --name "nonexistent"
expect_succ test "$(echo "$OUTPUT" | jq -r '.|length')" = "0"

# Test showing a specific blocklist entry
expect_succ pulp python repository blocklist show --repository "cli_test_python_blocklist" --href "$ENTRY_HREF"
test "$(echo "$OUTPUT" | jq -r '.name')" = "pkg"
test "$(echo "$OUTPUT" | jq -r '.version')" = "null"
expect_succ pulp python repository blocklist show --repository "cli_test_python_blocklist" --name "pkg"
test "$(echo "$OUTPUT" | jq -r '.pulp_href')" = "$ENTRY_HREF"

# Test input validation
expect_fail pulp python repository blocklist show --repository "cli_test_python_blocklist" --version "1.0" --filename "pkg-1.0.tar.gz"
expect_fail pulp python repository blocklist show --repository "cli_test_python_blocklist" --version "1.0"
expect_fail pulp python repository blocklist show --repository "cli_test_python_blocklist" --name "pkg" --filename "pkg-1.0.tar.gz"

# Test removing blocklist entries
expect_succ pulp python repository blocklist remove --repository "cli_test_python_blocklist" --href "$ENTRY_HREF"
expect_succ pulp python repository blocklist remove --repository "cli_test_python_blocklist" --name "pkg" --version "2.0"
expect_succ pulp python repository blocklist remove --repository "cli_test_python_blocklist" --filename "pkg-3.0.tar.gz"
expect_succ pulp python repository blocklist list --repository "cli_test_python_blocklist"
expect_succ test "$(echo "$OUTPUT" | jq -r '.|length')" = "0"

expect_succ pulp python repository destroy --name "cli_test_python_blocklist"
