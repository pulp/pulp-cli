#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "ansible" || exit 3

cleanup() {
  pulp ansible repository destroy --name "cli_test_ansible_repository" || true
  pulp orphan cleanup || true
}
trap cleanup EXIT

# Test ansible collection-version upload
wget "https://galaxy.ansible.com/download/ansible-posix-1.3.0.tar.gz"
sha256=$(sha256sum ansible-posix-1.3.0.tar.gz | cut -d' ' -f1)

expect_succ pulp ansible content upload --file "ansible-posix-1.3.0.tar.gz"
expect_succ pulp artifact list --sha256 "$sha256"
test "$(echo "$OUTPUT" | jq -r length)" -eq "1"
expect_succ pulp ansible content list --name "posix" --namespace "ansible" --version "1.3.0"
test "$(echo "$OUTPUT" | jq -r length)" -eq "1"
content_href="$(echo "$OUTPUT" | jq -r .[0].pulp_href)"
expect_succ pulp ansible content show --href "$content_href"

# Test ansible role upload
wget "https://github.com/ansible/ansible-kubernetes-modules/archive/v0.0.1.tar.gz"
sha2256=$(sha256sum v0.0.1.tar.gz | cut -d' ' -f1)

expect_succ pulp ansible content --type "role" upload --file "v0.0.1.tar.gz" --name "kubernetes-modules" --namespace "ansible" --version "0.0.1"
expect_succ pulp artifact list --sha256 "$sha2256"
test "$(echo "$OUTPUT" | jq -r length)" -eq "1"
expect_succ pulp ansible content --type "role" list --name "kubernetes-modules" --namespace "ansible" --version "0.0.1"
test "$(echo "$OUTPUT" | jq -r length)" -eq "1"
content2_href="$(echo "$OUTPUT" | jq -r .[0].pulp_href)"
expect_succ pulp ansible content --type "role" show --href "$content2_href"

# Test ansible signature upload
if pulp debug has-plugin --name "ansible" --min-version "0.13.0.dev"
then
  expect_succ pulp ansible content --type "signature" list
  tar --extract --file="ansible-posix-1.3.0.tar.gz" "MANIFEST.json"
  collection_path="$(realpath 'MANIFEST.json')"
  signature_path="$("$(dirname "$(dirname "$(dirname "$(realpath "$0")")")")"/assets/sign_detached.sh "$collection_path" | jq -r .signature)"
  expect_succ pulp ansible content --type "signature" upload --file "$signature_path" --collection "$content_href"
  expect_succ pulp ansible content --type "signature" list --collection "$content_href" --pubkey-fingerprint "6EDF301256480B9B801EBA3D05A5E6DA269D9D98"
  test "$(echo "$OUTPUT" | jq -r length)" -eq "1"
  content3_href="$(echo "$OUTPUT" | jq -r .[0].pulp_href)"
  expect_succ pulp ansible content --type "signature" show --href "$content3_href"
fi

# New content commands
expect_succ pulp ansible repository create --name "cli_test_ansible_repository"
expect_succ pulp ansible repository content add --repository "cli_test_ansible_repository" --name "posix" --namespace "ansible" --version "1.3.0"
expect_succ pulp ansible repository content list --repository "cli_test_ansible_repository" --version 1
test "$(echo "$OUTPUT" | jq -r length)" -eq "1"
expect_succ pulp ansible repository content --type "role" add --repository "cli_test_ansible_repository" --name "kubernetes-modules" --namespace "ansible" --version "0.0.1"
expect_succ pulp ansible repository content --type "role" list --repository "cli_test_ansible_repository" --version 2
test "$(echo "$OUTPUT" | jq -r length)" -eq "1"

if pulp debug has-plugin --name "core" --min-version "3.11.0"
then
  expect_succ pulp ansible repository content list --repository "cli_test_ansible_repository" --version 2 --all-types
  test "$(echo "$OUTPUT" | jq -r length)" -eq "2"
fi

expect_succ pulp ansible repository content remove --repository "cli_test_ansible_repository" --href "$content_href"
expect_succ pulp ansible repository content remove --repository "cli_test_ansible_repository" --href "$content2_href"
expect_succ pulp ansible repository content list --repository "cli_test_ansible_repository"
test "$(echo "$OUTPUT" | jq -r length)" -eq "0"
