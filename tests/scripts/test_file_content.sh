#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")/config.source"

cleanup() {
  rm test.txt
  pulp orphans delete
}
trap cleanup EXIT

# Test file upload
dd if=/dev/urandom of=test.txt bs=2MiB count=1
sha256=$(sha256sum test.txt | cut -d' ' -f1)

expect_succ pulp file content upload --file test.txt --relative-path upload_test/test.txt
expect_succ pulp artifact list --sha256 "$sha256"
test "$(echo "$OUTPUT" | jq -r length)" -eq "1"
expect_succ pulp file content list --sha256 "$sha256"
test "$(echo "$OUTPUT" | jq -r length)" -eq "1"
content_href="$(echo "$OUTPUT" | jq -r .[0].pulp_href)"
expect_succ pulp file content show --href "$content_href"

# Test creation from artifact
dd if=/dev/urandom of=test.txt bs=2MiB count=1
sha256=$(sha256sum test.txt | cut -d' ' -f1)

expect_succ pulp artifact upload --file test.txt
expect_succ pulp file content create --sha256 "$sha256" --relative-path upload_test/test.txt
