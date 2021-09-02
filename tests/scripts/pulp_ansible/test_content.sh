#!/bin/bash

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "ansible" || exit 3

cleanup() {
  pulp orphans delete || true
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
