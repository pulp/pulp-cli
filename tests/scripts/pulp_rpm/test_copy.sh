#!/bin/bash
# src1 src2 dest1 dest2 pkg advisory

# shellcheck source=tests/scripts/config.source
. "$(dirname "$(dirname "$(realpath "$0")")")"/config.source

pulp debug has-plugin --name "rpm" || exit 23
BASE_NAME="cli_test_rpm_copy"

cleanup() {
  for pre in "src" "dst"; do
    for inst in {1..2}; do
      pulp rpm repository destroy --name "${pre}_${BASE_NAME}_${inst}"
    done
  done
  pulp rpm remote destroy --name "${BASE_NAME}"
  #rm -f ./cli_copy_test.json
}
trap cleanup EXIT

# Create one remote
expect_succ pulp rpm remote create --name "${BASE_NAME}" --url "${RPM_REMOTE_URL}" --policy on_demand

# Create 2 src and 2 dest repos and record facts about them
declare -A repo_hrefs
declare -A vers_hrefs
for pre in "src" "dst"; do
  for inst in {1..2}; do
    echo "${pre}/${inst}"
    expect_succ pulp rpm repository create --name "${pre}_${BASE_NAME}_${inst}" --remote "${BASE_NAME}" --no-autopublish
    #can't double-subscript
    repo_hrefs["${pre}_${BASE_NAME}_${inst}"]="$(echo "$OUTPUT" | jq  -r '.pulp_href')"
    vers_hrefs["${pre}_${BASE_NAME}_${inst}"]="$(echo "$OUTPUT" | jq  '.latest_version_href')"
    echo "REPO ${repo_hrefs["${pre}_${BASE_NAME}_${inst}"]}, VERS ${vers_hrefs["${pre}_${BASE_NAME}_${inst}"]}"
  done
done
# sync the src repos (only)
for inst in {1..2}; do
  echo "SYNC src_${BASE_NAME}_${inst}}"
  expect_succ pulp rpm repository sync --repository "src_${BASE_NAME}_${inst}"
done

# Find and remember on RPM HREF and one Advisory HREF from src1
rpm_href="$(pulp rpm content -t package list --name bear --version 4.1 --release 1 --field pulp_href | jq  '.[0].pulp_href')"
echo "RPM ${rpm_href}"
advisory_href="$(pulp rpm content -t advisory list --id RHEA-2012:0055 --field pulp_href | jq  '.[0].pulp_href')"
echo "ADVISORY ${advisory_href}"

# copy src1 to dest1
cat << EOF >  ./cli_copy_test.json
[
  {
    "source_repo_version": ${vers_hrefs["src_${BASE_NAME}_1"]},
    "dest_repo": "${repo_hrefs["dst_${BASE_NAME}_1"]}"
  }
]
EOF
expect_succ pulp rpm copy --config @./cli_copy_test.json

# copy 2 units from src1 to dest1
cat << EOF >  ./cli_copy_test.json
[
  {
    "source_repo_version": ${vers_hrefs["src_${BASE_NAME}_1"]},
    "dest_repo": "${repo_hrefs["dst_${BASE_NAME}_1"]}",
    "content": [${rpm_href}, ${advisory_href}]
  }
]
EOF
cat ./cli_copy_test.json
expect_succ pulp rpm copy --config @./cli_copy_test.json

# copy 2 units from src1 to dest1 based on dest1-version/0/
cat << EOF >  ./cli_copy_test.json
[
  {
    "source_repo_version": ${vers_hrefs["src_${BASE_NAME}_1"]},
    "dest_repo": "${repo_hrefs["dst_${BASE_NAME}_1"]}",
    "dest_base_version": 0,
    "content": [${rpm_href}, ${advisory_href}]
  }
]
EOF
expect_succ pulp rpm copy --config @./cli_copy_test.json

# multi-repo copy
cat << EOF >  ./cli_copy_test.json
[
  {
    "source_repo_version": ${vers_hrefs["src_${BASE_NAME}_1"]},
    "dest_repo": "${repo_hrefs["dst_${BASE_NAME}_1"]}",
    "content": [${rpm_href}, ${advisory_href}]
  },
  {
    "source_repo_version": ${vers_hrefs["src_${BASE_NAME}_2"]},
    "dest_repo": "${repo_hrefs["dst_${BASE_NAME}_2"]}",
    "content": []
  }
]
EOF
expect_succ pulp rpm copy --config @./cli_copy_test.json


