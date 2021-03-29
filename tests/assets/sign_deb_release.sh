#!/bin/bash

set -e

RELEASE_FILE="$(/usr/bin/readlink -f "$1")"
OUTPUT_DIR="$(/usr/bin/mktemp -d)"
DETACHED_SIGNATURE_PATH="${OUTPUT_DIR}/Release.gpg"
INLINE_SIGNATURE_PATH="${OUTPUT_DIR}/InRelease"
GPG_KEY_ID="Pulp QE"

# Create a detached signature
/usr/bin/gpg --batch --armor --digest-algo SHA256 \
  --detach-sign \
  --output "${DETACHED_SIGNATURE_PATH}" \
  --local-user "${GPG_KEY_ID}" \
  "${RELEASE_FILE}"

# Create an inline signature
/usr/bin/gpg --batch --armor --digest-algo SHA256 \
  --clearsign \
  --output "${INLINE_SIGNATURE_PATH}" \
  --local-user "${GPG_KEY_ID}" \
  "${RELEASE_FILE}"

echo "{" \
       \"signatures\": "{" \
         \"inline\": \""${INLINE_SIGNATURE_PATH}"\", \
         \"detached\": \""${DETACHED_SIGNATURE_PATH}"\" \
       "}" \
     "}"
