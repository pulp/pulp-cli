#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "python" --min-version "3.1.0.dev" || exit 3

cleanup() {
  pulp python remote destroy --name "cli_test_python_remote" || true
  pulp python remote destroy --name "cli_test_complex_remote" || true
  rm "python_test_requirements.txt" "python_test_requirements2.txt"
}
trap cleanup EXIT

expect_succ pulp python remote list

expect_succ pulp python remote create --name "cli_test_python_remote" --url "$PYTHON_REMOTE_URL"

# Update includes using requirements file
cat <<EOT >> python_test_requirements.txt
# Hello there!
Django>=4.0  # Comments don't affect it
shelf-reader
-r python_test_requirements2.txt  # Can recursively read requirements files
EOT

cat <<EOT >> python_test_requirements2.txt
# Hi there!
pulp_python
EOT

expect_succ pulp python remote update --name "cli_test_python_remote" --includes "@python_test_requirements.txt"
expect_succ pulp python remote show --name "cli_test_python_remote"
test "$(echo "$OUTPUT" | jq -r .includes[0])" = "Django>=4.0"
test "$(echo "$OUTPUT" | jq -r .includes[1])" = "shelf-reader"
test "$(echo "$OUTPUT" | jq -r .includes[2])" = "pulp_python"
expect_succ pulp python remote list

if [ "$(pulp debug has-plugin --name "python" --min-version "3.2.0.dev")" = "true" ]
  then
    expect_succ pulp python remote create --name "cli_test_complex_remote" --url "$PYTHON_REMOTE_URL" --keep-latest-packages 3 --package-types '["sdist", "bdist_wheel"]' --exclude-platforms '["windows"]'
  else
    expect_fail pulp python remote create --name "cli_test_complex_remote" --url "$PYTHON_REMOTE_URL" --keep-latest-packages 3 --package-types '["sdist", "bdist_wheel"]' --exclude-platforms '["windows"]'
fi
expect_succ pulp python remote destroy --name "cli_test_python_remote"
