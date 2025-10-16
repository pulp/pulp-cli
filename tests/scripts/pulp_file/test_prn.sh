#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "core" --specifier ">=3.63.0" || exit 23
pulp debug has-plugin --name "file" || exit 23

cleanup() {
  pulp file distribution destroy --name "cli_test_file_prn_distribution"  || true
  pulp file repository destroy --name "cli_test_file_prn_repository" || true
  pulp file remote destroy --name "cli_test_file_prn_remote" || true
}
trap cleanup EXIT

cleanup

# Prepare
expect_succ pulp file remote create --name "cli_test_file_prn_remote" --url "$FILE_REMOTE_URL"
remote_prn=$(echo "${OUTPUT}" | jq -r .prn)
expect_succ pulp file repository create --name "cli_test_file_prn_repository"
repository_prn=$(echo "${OUTPUT}" | jq -r .prn)

# Test show-by-PRN
expect_succ pulp -v file remote show --remote "${remote_prn}"
expect_succ pulp -v file repository show --repository "${repository_prn}"

# Test fail to show by not-a-PRN
expect_fail pulp -v file remote show --remote prn:not:a:prn

# Test fail-to-show by not the right *kind* of PRN
expect_fail pulp -v file remote show --remote "${repository_prn}"

# Test sync
expect_succ pulp -v file repository sync --repository "${repository_prn}" --remote "${remote_prn}"
file_prn=$(pulp file content list --limit 1 --offset 0 | jq -r .[].prn)

# Test update
expect_succ pulp -v file repository update --repository "${repository_prn}" --remote "${remote_prn}"

# Test version
expect_succ pulp file repository version list --repository "${repository_prn}"
expect_succ pulp file repository version show --repository "${repository_prn}" --version 1

# Test publication
expect_succ pulp file publication create --repository "${repository_prn}"
publication_prn=$(echo "${OUTPUT}" | jq -r .prn)

# Test distribution
expect_succ pulp file distribution create --name "cli_test_file_prn_distribution" --base-path "cli_test_file_prn_distribution" --publication "${publication_prn}"

# Test looking up "hrefs" using prn:
# (Note: this only works when we have the context and prn__in=[] is supported
# pulp show --href won't work unless/until core exposes a "contextless" /pulp/api/v3/prn/ API
expect_succ pulp file publication show --href "${publication_prn}"
expect_succ pulp file content show --href "${file_prn}"

