#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(realpath "$0")")/config.source"

cleanup() {
  rm test_1.txt test_2.txt test_3.txt
  rm add_content.json remove_content.json
  pulp file repository destroy --name "cli_test_file_repository" || true
  pulp orphans delete || true
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

expect_succ pulp file repository create --name "cli_test_file_repository"

# Add content using JSON string
expect_succ pulp file repository modify --name "cli_test_file_repository" --add-content "[{\"sha256\":\"$sha256_1\",\"relative_path\":\"upload_test/test_1.txt\"},{\"sha256\":\"$sha256_2\",\"relative_path\":\"upload_test/test_2.txt\"},{\"sha256\":\"$sha256_3\",\"relative_path\":\"upload_test/test_3.txt\"}]"
expect_succ pulp file repository modify --name "cli_test_file_repository" --remove-content "[{\"sha256\":\"$sha256_1\",\"relative_path\":\"upload_test/test_1.txt\"},{\"sha256\":\"$sha256_2\",\"relative_path\":\"upload_test/test_2.txt\"},{\"sha256\":\"$sha256_3\",\"relative_path\":\"upload_test/test_3.txt\"}]"

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

expect_succ pulp file repository modify --name "cli_test_file_repository" --add-content "@add_content.json" --base-version 0
expect_succ pulp file repository modify --name "cli_test_file_repository" --remove-content "@remove_content.json"
