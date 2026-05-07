#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "python" --specifier ">=3.30.0" || exit 23

cleanup() {
  pulp python repository destroy --name "cli_test_python_blocklist" || true
}
trap cleanup EXIT

expect_succ pulp python repository create --name "cli_test_python_blocklist"

# Test adding a blocklist entry by package name
expect_succ pulp python repository blocklist add --repository "cli_test_python_blocklist" --name "pkg"
test "$(echo "$OUTPUT" | jq -r '.name')" = "pkg"
test "$(echo "$OUTPUT" | jq -r '.version')" = "null"
test "$(echo "$OUTPUT" | jq -r '.filename')" = "null"
ENTRY_HREF="$(echo "$OUTPUT" | jq -r '.pulp_href')"

# Test listing blocklist entries
expect_succ pulp python repository blocklist list --repository "cli_test_python_blocklist"
expect_succ test "$(echo "$OUTPUT" | jq -r '.|length')" = "1"
expect_succ pulp python repository blocklist list --repository "cli_test_python_blocklist" --name "pkg"
expect_succ test "$(echo "$OUTPUT" | jq -r '.|length')" = "1"
expect_succ pulp python repository blocklist list --repository "cli_test_python_blocklist" --name "nonexistent"
expect_succ test "$(echo "$OUTPUT" | jq -r '.|length')" = "0"

# Test showing a specific blocklist entry
expect_succ pulp python repository blocklist show --repository "cli_test_python_blocklist" --href "$ENTRY_HREF"
expect_succ test "$(echo "$OUTPUT" | jq -r '.name')" = "pkg"
expect_succ pulp python repository blocklist show --repository "cli_test_python_blocklist" --name "pkg"
expect_succ test "$(echo "$OUTPUT" | jq -r '.name')" = "pkg"

# Test remove validation
expect_fail pulp python repository blocklist remove --repository "cli_test_python_blocklist" --version "1.0" --filename "pkg-1.0.tar.gz"
expect_fail pulp python repository blocklist remove --repository "cli_test_python_blocklist" --version "1.0"
expect_fail pulp python repository blocklist remove --repository "cli_test_python_blocklist" --name "pkg" --filename "pkg-1.0.tar.gz"

# Test removing a blocklist entry by href
expect_succ pulp python repository blocklist remove --repository "cli_test_python_blocklist" --href "$ENTRY_HREF"
expect_succ pulp python repository blocklist list --repository "cli_test_python_blocklist"
expect_succ test "$(echo "$OUTPUT" | jq -r '.|length')" = "0"

# Test removing a blocklist entry by package name + version
expect_succ pulp python repository blocklist add --repository "cli_test_python_blocklist" --name "pkg" --version "2.0"
expect_succ pulp python repository blocklist remove --repository "cli_test_python_blocklist" --name "pkg" --version "2.0"
expect_succ pulp python repository blocklist list --repository "cli_test_python_blocklist"
expect_succ test "$(echo "$OUTPUT" | jq -r '.|length')" = "0"

# Test removing a blocklist entry by package filename
expect_succ pulp python repository blocklist add --repository "cli_test_python_blocklist" --filename "pkg-3.0.tar.gz"
expect_succ pulp python repository blocklist remove --repository "cli_test_python_blocklist" --filename "pkg-3.0.tar.gz"
expect_succ pulp python repository blocklist list --repository "cli_test_python_blocklist"
expect_succ test "$(echo "$OUTPUT" | jq -r '.|length')" = "0"

expect_succ pulp python repository destroy --name "cli_test_python_blocklist"
