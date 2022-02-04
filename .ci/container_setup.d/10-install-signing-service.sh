#!/bin/sh

set -eu

if pulp --format none --refresh-api --base-url "http://localhost:8080" ${PULP_API_ROOT:+--api-root "${PULP_API_ROOT}"} --username "admin" --password "password" debug has-plugin --name "deb"
then
  echo "Setup a signing service"
  "${CONTAINER_RUNTIME}" exec -i "pulp-ephemeral" bash -c "cat > /root/sign_deb_release.sh" < "${BASEPATH}/../tests/assets/sign_deb_release.sh"
  "${CONTAINER_RUNTIME}" exec -i "pulp-ephemeral" bash -c "cat > /tmp/setup_signing_service.py" < "${BASEPATH}/../tests/assets/setup_signing_service.py"
  curl -L https://github.com/pulp/pulp-fixtures/raw/master/common/GPG-KEY-pulp-qe | "${CONTAINER_RUNTIME}" exec -i "pulp-ephemeral" bash -c "cat > /tmp/GPG-KEY-pulp-qe"
  curl -L https://github.com/pulp/pulp-fixtures/raw/master/common/GPG-PRIVATE-KEY-pulp-qe | "${CONTAINER_RUNTIME}" exec -i "pulp-ephemeral" gpg --import
  echo "6EDF301256480B9B801EBA3D05A5E6DA269D9D98:6:" | "${CONTAINER_RUNTIME}" exec -i "pulp-ephemeral" gpg --import-ownertrust
  "${CONTAINER_RUNTIME}" exec "pulp-ephemeral" chmod a+x /root/sign_deb_release.sh /tmp/setup_signing_service.py
  "${CONTAINER_RUNTIME}" exec "pulp-ephemeral" /tmp/setup_signing_service.py /root/sign_deb_release.sh /tmp/GPG-KEY-pulp-qe
fi
