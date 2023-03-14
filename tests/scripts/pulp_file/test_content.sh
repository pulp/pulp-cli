#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "file" || exit 23

cleanup() {
  pulp file repository destroy --name "cli_test_file_repository" || true
  pulp orphan cleanup || true
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

# Test small file upload
dd if=/dev/urandom of=test.txt bs=64 count=1
sha256=$(sha256sum test.txt | cut -d' ' -f1)

expect_succ pulp file content upload --file test.txt --relative-path upload_test/test.txt
expect_succ pulp file content list --sha256 "$sha256"
test "$(echo "$OUTPUT" | jq -r length)" -eq "1"

# Test creation from artifact
dd if=/dev/urandom of=test.txt bs=2MiB count=1
sha256=$(sha256sum test.txt | cut -d' ' -f1)

expect_succ pulp artifact upload --file test.txt
expect_succ pulp file content create --sha256 "$sha256" --relative-path upload_test/test.txt

# Old content commands
expect_succ pulp file repository create --name "cli_test_file_repository"
expect_succ pulp file repository add --repository "cli_test_file_repository" --sha256 "$sha256" --relative-path upload_test/test.txt
expect_succ pulp file repository add --name "cli_test_file_repository" --sha256 "$sha256" --relative-path upload_test/test.txt --base-version 0
expect_succ pulp file repository remove --repository "cli_test_file_repository" --sha256 "$sha256" --relative-path upload_test/test.txt
expect_succ pulp file repository remove --name "cli_test_file_repository" --sha256 "$sha256" --relative-path upload_test/test.txt --base-version 1

# New content commands
expect_succ pulp file repository content add --repository "cli_test_file_repository" --sha256 "$sha256" --relative-path upload_test/test.txt
expect_succ pulp file repository content add --repository "cli_test_file_repository" --sha256 "$sha256" --relative-path upload_test/test.txt --base-version 0
expect_succ pulp file repository content list --repository "cli_test_file_repository" --version 1
test "$(echo "$OUTPUT" | jq -r length)" -eq "1"
expect_succ pulp file repository content list --repository "cli_test_file_repository" --all-types

expect_succ pulp file repository content remove --repository "cli_test_file_repository" --sha256 "$sha256" --relative-path upload_test/test.txt
expect_succ pulp file repository content list --repository "cli_test_file_repository"
test "$(echo "$OUTPUT" | jq -r length)" -eq "0"

# Create and add to repository in one command
expect_succ pulp file content create --sha256 "$sha256" --relative-path upload_test/test2.txt --repository "cli_test_file_repository"
expect_succ pulp file content upload --file test.txt --relative-path upload_test/test3.txt --repository "cli_test_file_repository"
expect_succ pulp file repository content list --repository "cli_test_file_repository"
test "$(echo "$OUTPUT" | jq -r '[.[]|.relative_path]|sort|join(" ")')" = "upload_test/test2.txt upload_test/test3.txt"

expect_succ pulp content list
test "$(echo "$OUTPUT" | jq -r length)" -gt "0"

expect_succ pulp repository version list
expect_succ pulp repository version list --content "[]"
expect_succ pulp repository version list --content "$(jq -R '[.]' <<<"$content_href")"
