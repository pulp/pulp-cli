#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

cleanup() {
  pulp orphans delete
}
trap cleanup EXIT

dd if=/dev/urandom of=test.txt bs=2MiB count=1
sha256=$(sha256sum test.txt | cut -d' ' -f1)

expect_succ pulp artifact upload --file test.txt
expect_succ pulp artifact list --sha256 "$sha256"
test "$(echo "$OUTPUT" | jq -r length)" -eq "1"

# attempt to reupload the file
expect_succ pulp artifact upload --file test.txt
