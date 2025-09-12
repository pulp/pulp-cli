#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source


dd if=/dev/urandom of=test.txt bs=2MiB count=1
dd if=/dev/urandom of=test2.txt bs=10KiB count=1
sha256=$(sha256sum test.txt | cut -d' ' -f1)
sha2256=$(sha256sum test2.txt | cut -d' ' -f1)

expect_succ pulp artifact upload --file test.txt
expect_succ pulp artifact list --sha256 "$sha256"
test "$(echo "$OUTPUT" | jq -r length)" -eq "1"

expect_succ pulp artifact upload --file test2.txt --chunk-size 1KB
expect_fail pulp artifact upload --file test2.txt --chunk-size 1KKB
expect_succ pulp artifact list --sha256 "$sha2256"
test "$(echo "$OUTPUT" | jq -r length)" -eq "1"

# attempt to reupload the file
expect_succ pulp artifact upload --file test.txt
