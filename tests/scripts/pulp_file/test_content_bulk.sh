#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "file" || exit 23

cleanup() {
  pulp file repository destroy --name "cli_test_file_content_bulk_repository" || true
}
trap cleanup EXIT

# Test bulk add to repository
dd if=/dev/urandom of=test_1.txt bs=2MiB count=1
sha256_1=$(sha256sum test_1.txt | cut -d' ' -f1)
dd if=/dev/urandom of=test_2.txt bs=2MiB count=1
sha256_2=$(sha256sum test_2.txt | cut -d' ' -f1)
dd if=/dev/urandom of=test_3.txt bs=2MiB count=1
sha256_3=$(sha256sum test_3.txt | cut -d' ' -f1)

expect_succ pulp artifact upload --file test_1.txt
expect_succ pulp artifact upload --file test_2.txt
expect_succ pulp artifact upload --file test_3.txt
expect_succ pulp file content create --sha256 "$sha256_1" --relative-path upload_test/test_1.txt
expect_succ pulp file content create --sha256 "$sha256_2" --relative-path upload_test/test_2.txt
expect_succ pulp file content create --sha256 "$sha256_3" --relative-path upload_test/test_3.txt

expect_succ pulp file repository create --name "cli_test_file_content_bulk_repository"

# Test invalid json input
expect_fail pulp file repository content modify --repository "cli_test_file_content_bulk_repository" --add-content "{\"sha256\":\"$sha256_1\",\"relative_path\":\"upload_test/test_1.txt\"}"
echo "${ERROUTPUT}" | grep -q "should be instance of 'list'"
expect_fail pulp file repository content modify --repository "cli_test_file_content_bulk_repository" --add-content "[{\"relative_path\":\"upload_test/test_1.txt\"}]"
echo "${ERROUTPUT}" | grep -q "Missing key: 'sha256'"
expect_fail pulp file repository content modify --repository "cli_test_file_content_bulk_repository" --add-content "[{\"sha256\":\"$sha256_1\",\"relative_path\":\"upload_test/test_1.txt\", \"sha128\":\"abcd\"}]"
echo "${ERROUTPUT}" | grep -q "Wrong key 'sha128' in"
expect_fail pulp file repository content modify --repository "cli_test_file_content_bulk_repository" --add-content "[{\"sha256\":1234567890,\"relative_path\":\"upload_test/test_1.txt\"}]"
echo "${ERROUTPUT}" | grep -q "should be instance of 'str'"
expect_fail pulp file repository content modify --repository "cli_test_file_content_bulk_repository" --add-content "[{\"sha256\":\"$sha256_1\",\"relative_path\":\"\"}]"
echo "${ERROUTPUT}" | grep -q "Key 'relative_path' error:"

# Add content using JSON file
cat <<EOT >> add_content.json
[
    {
        "sha256":"$sha256_1",
        "relative_path":"upload_test/test_1.txt"
    },
    {
        "sha256":"$sha256_2",
        "relative_path":"upload_test/test_2.txt"
    },
    {
        "sha256":"$sha256_3",
        "relative_path":"upload_test/test_3.txt"
    }
]
EOT
cp add_content.json remove_content.json

# New Content commands
expect_succ pulp file repository content modify --repository "cli_test_file_content_bulk_repository" --add-content "[{\"sha256\":\"$sha256_1\",\"relative_path\":\"upload_test/test_1.txt\"},{\"sha256\":\"$sha256_2\",\"relative_path\":\"upload_test/test_2.txt\"},{\"sha256\":\"$sha256_3\",\"relative_path\":\"upload_test/test_3.txt\"}]"
expect_succ pulp file repository content list --repository "cli_test_file_content_bulk_repository"
test "$(echo "$OUTPUT" | jq -r length)" -eq "3"
expect_succ pulp file repository content modify --repository "cli_test_file_content_bulk_repository" --remove-content "@remove_content.json"
expect_succ pulp file repository content list --repository "cli_test_file_content_bulk_repository"
test "$(echo "$OUTPUT" | jq -r length)" -eq "0"
