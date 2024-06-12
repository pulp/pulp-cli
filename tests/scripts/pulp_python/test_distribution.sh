#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "python" || exit 23

cleanup() {
  pulp python repository destroy --name "cli_test_python_repository" || true
  pulp python remote destroy --name "cli_test_python_remote" || true
  pulp python distribution destroy --name "cli_test_python_distro" || true
  pulp orphan cleanup || true
}
trap cleanup EXIT

if [ "$VERIFY_SSL" = "false" ]
then
  curl_opt=("-k")
else
  if [ "${PULP_CA_BUNDLE:+x}" ]
  then
    curl_opt=("--cacert" "${PULP_CA_BUNDLE}")
  else
    curl_opt=()
  fi
fi

expect_succ pulp python remote create --name "cli_test_python_remote" --url "$PYTHON_REMOTE_URL" --includes '["shelf-reader"]'
expect_succ pulp python repository create --name "cli_test_python_repository" --remote "cli_test_python_remote"
expect_succ pulp python repository sync --repository "cli_test_python_repository"
expect_succ pulp python publication create --repository "cli_test_python_repository"
PUBLICATION_HREF=$(echo "$OUTPUT" | jq -r .pulp_href)

expect_succ pulp python distribution create \
  --name "cli_test_python_distro" \
  --base-path "wrong_path" \
  --publication "$PUBLICATION_HREF"
HREF="$(echo "$OUTPUT" | jq -r '.pulp_href')"
expect_succ pulp python distribution update \
  --distribution "$HREF" \
  --publication ""
expect_succ pulp python distribution update \
  --distribution "cli_test_python_distro" \
  --base-path "cli_test_python_distro" \
  --publication "$PUBLICATION_HREF"

expect_succ curl "${curl_opt[@]}" --head --fail "$PULP_BASE_URL/pypi/cli_test_python_distro/simple/"
expect_succ pulp python distribution update \
--name "cli_test_python_distro" \
--repository "cli_test_python_repository" \
--block-uploads

expect_succ pulp python distribution update \
--name "cli_test_python_distro" \
--remote "cli_test_python_remote"

expect_succ pulp python distribution destroy --distribution "cli_test_python_distro"
