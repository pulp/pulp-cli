#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "python" || exit 23

cleanup() {
  pulp python repository destroy --name "cli_test_python_publication_repository" || true
  pulp python remote destroy --name "cli_test_python_publication_remote" || true
}
trap cleanup EXIT

pulp python remote create --name "cli_test_python_publication_remote" --url "$PYTHON_REMOTE_URL"
pulp python repository create --name "cli_test_python_publication_repository" --remote "cli_test_python_publication_remote"
pulp python repository sync --repository "cli_test_python_publication_repository"

expect_succ pulp python publication create --repository "cli_test_python_publication_repository"
PUBLICATION_HREF="$(echo "$OUTPUT" | jq -r .pulp_href)"
expect_succ pulp python publication destroy --href "$PUBLICATION_HREF"
expect_succ pulp python publication create --repository "cli_test_python_publication_repository" --version 0
PUBLICATION_HREF="$(echo "$OUTPUT" | jq -r .pulp_href)"
expect_succ pulp python publication destroy --href "$PUBLICATION_HREF"
