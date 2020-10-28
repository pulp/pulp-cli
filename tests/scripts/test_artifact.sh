#!/bin/sh

. "$(dirname "$(realpath "$0")")/config.source"

cleanup() {
  rm test.txt
  pulp_cli orphans delete
}
trap cleanup EXIT

dd if=/dev/urandom of=test.txt bs=2MiB count=1
sha256=$(sha256sum test.txt | cut -d' ' -f1)

pulp_cli artifact upload --file test.txt
test "$(pulp_cli artifact list --sha256 "$sha256" | jq -r length)" -eq "1"
