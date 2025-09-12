#!/bin/bash

set -eu
# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "ansible" || exit 23

cleanup() {
  pulp ansible repository destroy --name "cli_test_ansible_content_repository" || true
  pulp ansible repository destroy --name "cli_test_ansible_content_repository_verify" || true
  pulp ansible repository destroy --name "cli_test_ansible_content_repository_upload" || true
}
trap cleanup EXIT


if pulp debug has-plugin --name "ansible" --specifier ">=0.15.0"
then
  gpg --output pulp_pubkey.key --armor --export "pulp-fixture-signing-key"
  expect_succ pulp ansible repository create --name "cli_test_ansible_content_repository_verify" --gpgkey @pulp_pubkey.key
else
  expect_succ pulp ansible repository create --name "cli_test_ansible_content_repository_verify"
fi

# Test ansible collection-version upload
wget "https://galaxy.ansible.com/download/ansible-posix-1.3.0.tar.gz"
sha256=$(sha256sum ansible-posix-1.3.0.tar.gz | cut -d' ' -f1)

expect_succ pulp ansible repository create --name "cli_test_ansible_content_repository_upload"
expect_succ pulp ansible content upload --file "ansible-posix-1.3.0.tar.gz" --repository "cli_test_ansible_content_repository_upload"
expect_succ pulp artifact list --sha256 "$sha256"
test "$(echo "$OUTPUT" | jq -r length)" -eq "1"
expect_succ pulp ansible content list --name "posix" --namespace "ansible" --version "1.3.0"
test "$(echo "$OUTPUT" | jq -r length)" -eq "1"
content_href="$(echo "$OUTPUT" | jq -r .[0].pulp_href)"
expect_succ pulp ansible content show --href "$content_href"
expect_succ pulp ansible repository content list --repository "cli_test_ansible_content_repository_upload" --version 1
test "$(echo "$OUTPUT" | jq -r length)" -eq "1"

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
if pulp debug has-plugin --name "ansible" --specifier ">=0.13.0"
then
  expect_succ pulp ansible content --type "signature" list
  tar --extract --file="ansible-posix-1.3.0.tar.gz" "MANIFEST.json"
  collection_path="$(realpath 'MANIFEST.json')"
  signature_path="$("$(dirname "$(dirname "$(dirname "$(realpath "$0")")")")"/assets/sign_detached.sh "$collection_path" | jq -r .signature)"
  expect_succ pulp ansible content --type "signature" upload --file "$signature_path" --collection "$content_href" --repository "cli_test_ansible_content_repository_verify"
  expect_succ pulp ansible content --type "signature" list --collection "$content_href" --pubkey-fingerprint "0C1A894EBB86AFAE218424CADDEF3019C2D4A8CF"
  test "$(echo "$OUTPUT" | jq -r length)" -eq "1"
  content3_href="$(echo "$OUTPUT" | jq -r .[0].pulp_href)"
  expect_succ pulp ansible content --type "signature" show --href "$content3_href"
fi

# New content commands
expect_succ pulp ansible repository create --name "cli_test_ansible_content_repository"
expect_succ pulp ansible repository content add --repository "cli_test_ansible_content_repository" --name "posix" --namespace "ansible" --version "1.3.0"
expect_succ pulp ansible repository content list --repository "cli_test_ansible_content_repository" --version 1
test "$(echo "$OUTPUT" | jq -r length)" -eq "1"
expect_succ pulp ansible repository content --type "role" add --repository "cli_test_ansible_content_repository" --name "kubernetes-modules" --namespace "ansible" --version "0.0.1"
expect_succ pulp ansible repository content --type "role" list --repository "cli_test_ansible_content_repository" --version 2
test "$(echo "$OUTPUT" | jq -r length)" -eq "1"

if pulp debug has-plugin --name "core" --specifier ">=3.11.0"
then
  expect_succ pulp ansible repository content list --repository "cli_test_ansible_content_repository" --version 2 --all-types
  test "$(echo "$OUTPUT" | jq -r length)" -eq "2"
fi

expect_succ pulp ansible repository content remove --repository "cli_test_ansible_content_repository" --href "$content_href"
expect_succ pulp ansible repository content remove --repository "cli_test_ansible_content_repository" --href "$content2_href"
expect_succ pulp ansible repository content list --repository "cli_test_ansible_content_repository"
test "$(echo "$OUTPUT" | jq -r length)" -eq "0"
