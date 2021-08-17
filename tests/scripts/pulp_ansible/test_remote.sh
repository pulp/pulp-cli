#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "ansible" || exit 3

cleanup() {
  pulp ansible remote -t "role" destroy --name "cli_test_ansible_role_remote" || true
  pulp ansible remote -t "collection" destroy --name "cli_test_ansible_collection_remote" || true
  rm requirements.yml || true
}
trap cleanup EXIT

expect_succ pulp ansible remote list

expect_succ pulp ansible remote -t "role" create --name "cli_test_ansible_role_remote" --url "$ANSIBLE_ROLE_REMOTE_URL"
expect_succ pulp ansible remote -t "collection" create --name "cli_test_ansible_collection_remote" --url "$ANSIBLE_COLLECTION_REMOTE_URL"
expect_succ pulp ansible remote -t "role" list
expect_succ pulp ansible remote -t "collection" list
expect_succ pulp ansible remote -t "role" update --name "cli_test_ansible_role_remote" --download-concurrency "5"
expect_succ pulp ansible remote -t "collection" update --name "cli_test_ansible_collection_remote" --download-concurrency "5"
expect_fail pulp ansible remote -t "role" update --name "cli_test_ansible_role_remote" --requirements "collections:\n  - robertdebock.ansible_development_environment"
test "$ERROUTPUT" = "Error: Option requirements not valid for Role remote, see --help"
expect_succ pulp ansible remote -t "role" destroy --name "cli_test_ansible_role_remote"
expect_succ pulp ansible remote -t "collection" destroy --name "cli_test_ansible_collection_remote"

# test requirements file
echo "---
collections:
  - testing.ansible_testing_content
  - pulp.squeezer" > requirements.yml
expect_succ pulp ansible remote create --name "cli_test_ansible_collection_remote" \
  --requirements-file requirements.yml --url "$ANSIBLE_COLLECTION_REMOTE_URL"
