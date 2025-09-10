#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "ansible" --specifier ">=0.12.0" || exit 23
[ "$(pulp signing-service list --name "sign_ansible" | jq 'length')" = "1" ] || exit 23

cleanup() {
  pulp ansible remote -t "collection" destroy --name "cli_test_ansible_sign_remote" || true
  pulp ansible repository destroy --name "cli_test_ansible_sign_repository" || true
}
trap cleanup EXIT

# Prepare
expect_succ pulp ansible remote -t "collection" create --name "cli_test_ansible_sign_remote" \
--url "$ANSIBLE_COLLECTION_REMOTE_URL" --requirements "collections:
  - robertdebock.ansible_development_environment"
expect_succ pulp ansible repository create --name "cli_test_ansible_sign_repository"
HREF="$(echo "$OUTPUT" | jq -r '.pulp_href')"
expect_succ pulp ansible repository sync --repository "cli_test_ansible_sign_repository" --remote "cli_test_ansible_sign_remote"

# Test sign
expect_succ pulp ansible repository sign --repository "cli_test_ansible_sign_repository" --signing-service "sign_ansible"

# Verify sign
expect_succ pulp ansible repository version list --repository "$HREF"
test "$(echo "$OUTPUT" | jq -r length)" -eq 3
expect_succ pulp ansible repository version show --repository "cli_test_ansible_sign_repository" --version 2
test "$(echo "$OUTPUT" | jq -r '.content_summary.present."ansible.collection_signature".count')" -gt 0
