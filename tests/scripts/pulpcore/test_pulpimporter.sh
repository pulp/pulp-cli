#!/bin/sh

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "file" || exit 3

cleanup() {
  pulp exporter pulp destroy --name cli_test_exporter || true
  pulp importer pulp destroy --name cli_test_importer || true
  pulp file repository destroy --name dest1 || true
  pulp file repository destroy --name dest2 || true
  pulp file repository destroy --name src1 || true
  pulp file repository destroy --name src2 || true
  # Clean up export files
  [ -n "$EXPORT_TOC" ] && rm -f "$EXPORT_TOC"
  [ -n "$EXPORT_FILE" ] && rm -f "$EXPORT_FILE"
}
trap cleanup EXIT

expect_succ pulp file repository create --name dest1
expect_succ pulp file repository create --name dest2

# create, show, destroy
expect_succ pulp importer pulp create --name "cli_test_importer"
expect_succ pulp importer pulp show --name "cli_test_importer"
expect_succ pulp importer pulp list --name "cli_test_importer"
test "$(echo "$OUTPUT" | jq -r length)" -eq 1
expect_succ pulp importer pulp destroy --name "cli_test_importer"

# create with a repo mapping
expect_succ pulp importer pulp create --name "cli_test_importer" --repo-map src1 dest1
test "$(echo "$OUTPUT" | jq '.repo_mapping' | jq -r length)" -eq 1
test "$(echo "$OUTPUT" | jq '.repo_mapping.src1')" = "\"dest1\""

# update repo mapping
expect_succ pulp importer pulp update --name "cli_test_importer" --repo-map src1 dest1 --repo-map src2 dest2
test "$(echo "$OUTPUT" | jq '.repo_mapping' | jq -r length)" -eq 2
test "$(echo "$OUTPUT" | jq '.repo_mapping.src1')" = "\"dest1\""
test "$(echo "$OUTPUT" | jq '.repo_mapping.src2')" = "\"dest2\""
expect_succ pulp importer pulp destroy --name "cli_test_importer"

#
## Test imports
#
EXPORTER="cli_test_exporter"
IMPORTER="cli_test_importer"
PATH1="/tmp/exports"
expect_succ pulp file repository create --name src1
expect_succ pulp file repository create --name src2
expect_succ pulp exporter pulp create --name $EXPORTER --path $PATH1 --repository src1 file --repository src2 file
expect_succ pulp export pulp run --exporter $EXPORTER
EXPORT_TOC=$(echo "$OUTPUT" | jq -r '.toc_info.file')
EXPORT_FILE=$(echo "$EXPORT_TOC" | sed -e 's/-toc.json/.tar.gz/')

expect_succ pulp importer pulp create --name $IMPORTER --repo-map src1 dest1 --repo-map src2 dest2

# Test import
expect_succ pulp import pulp run --importer $IMPORTER  --toc "$EXPORT_TOC"
expect_succ pulp import pulp run --importer $IMPORTER  --path "$EXPORT_FILE"

# Test list imports
expect_succ pulp import pulp list --importer $IMPORTER

# Test delete import
expect_succ pulp import pulp list --importer $IMPORTER
HREF=$(echo "$OUTPUT" | jq -r '.[0].pulp_href')

# Test toc/path uniqueness
expect_fail pulp import pulp run --importer $IMPORTER  --toc "$EXPORT_TOC" --path "$EXPORT_FILE"
expect_fail pulp import pulp run --importer $IMPORTER

expect_succ pulp import pulp destroy --href "$HREF"
