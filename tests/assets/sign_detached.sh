#!/usr/bin/env bash

FILE_PATH=$1
SIGNATURE_PATH="$1.asc"
: "${PULP_SIGNING_KEY_FINGERPRINT:="Pulp QE"}"

# Create a detached signature
gpg --quiet --batch --homedir ~/.gnupg/ --detach-sign --default-key "${PULP_SIGNING_KEY_FINGERPRINT}" \
   --armor --output "${SIGNATURE_PATH}" "${FILE_PATH}"

# Check the exit status
STATUS=$?
if [[ ${STATUS} -eq 0 ]]; then
   echo "{\"file\": \"${FILE_PATH}\", \"signature\": \"${SIGNATURE_PATH}\"}"
else
   exit ${STATUS}
fi
