#!/bin/bash

set -euv

# make sure this script runs at the repo root
cd "$(dirname "$(realpath -e "$0")")"/../..

REF="${1#refs/}"
REF_NAME="${REF#*/}"
REF_TYPE="${REF%%/*}"

mkdir ~/.ssh
echo "${PULP_DOCS_KEY}" > ~/.ssh/pulp-infra
chmod 600 ~/.ssh/pulp-infra

echo "docs.pulpproject.org,8.43.85.236 ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBGXG+8vjSQvnAkq33i0XWgpSrbco3rRqNZr0SfVeiqFI7RN/VznwXMioDDhc+hQtgVhd6TYBOrV07IMcKj+FAzg=" >> /home/runner/.ssh/known_hosts
chmod 644 /home/runner/.ssh/known_hosts

pip3 install -r doc_requirements.txt

eval "$(ssh-agent -s)" #start the ssh agent
ssh-add ~/.ssh/pulp-infra

make site

if [ "${REF_TYPE}" = "heads" ]
then
  [ "${REF_NAME}" = "main" ]
  # publish to docs.pulpproject.org/pulp_cli
  rsync -avzh site/ doc_builder_pulp_cli@docs.pulpproject.org:/var/www/docs.pulpproject.org/pulp_cli/
else
  [ "${REF_TYPE}" = "tags" ]
  # publish to docs.pulpproject.org/pulp_cli/en/{release}
  rsync -avzh site/ doc_builder_pulp_cli@docs.pulpproject.org:/var/www/docs.pulpproject.org/pulp_cli/en/"${REF_NAME}"
fi
