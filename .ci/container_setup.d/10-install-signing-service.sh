#!/bin/sh

set -eu

pulp --refresh-api --base-url "http://localhost:8080" ${PULP_API_ROOT:+--api-root "${PULP_API_ROOT}"} --username "admin" --password "password" debug has-plugin --name "deb" && HAS_DEB=true || HAS_DEB=""
pulp --base-url "http://localhost:8080" ${PULP_API_ROOT:+--api-root "${PULP_API_ROOT}"} --username "admin" --password "password" debug has-plugin --name "ansible" && HAS_ANSIBLE=true || HAS_ANSIBLE=""
if [ "$HAS_DEB" ] || [ "$HAS_ANSIBLE" ]
then
  echo "Setup the signing services"
  # Setup key on the Pulp container
  curl -L https://github.com/pulp/pulp-fixtures/raw/master/common/GPG-KEY-pulp-qe | "${CONTAINER_RUNTIME}" exec -i "pulp-ephemeral" bash -c "cat > /tmp/GPG-KEY-pulp-qe"
  curl -L https://github.com/pulp/pulp-fixtures/raw/master/common/GPG-PRIVATE-KEY-pulp-qe | "${CONTAINER_RUNTIME}" exec -i "pulp-ephemeral" gpg --import
  echo "6EDF301256480B9B801EBA3D05A5E6DA269D9D98:6:" | "${CONTAINER_RUNTIME}" exec -i "pulp-ephemeral" gpg --import-ownertrust
  # Setup key on the test machine
  curl -L https://github.com/pulp/pulp-fixtures/raw/master/common/GPG-KEY-pulp-qe | cat > /tmp/GPG-KEY-pulp-qe
  curl -L https://github.com/pulp/pulp-fixtures/raw/master/common/GPG-PRIVATE-KEY-pulp-qe | gpg --import
  echo "6EDF301256480B9B801EBA3D05A5E6DA269D9D98:6:" | gpg --import-ownertrust
  if [ "$HAS_DEB" ]
  then
    echo "Setup deb release signing service"
    "${CONTAINER_RUNTIME}" exec -i "pulp-ephemeral" bash -c "cat > /root/sign_deb_release.sh" < "${BASEPATH}/../tests/assets/sign_deb_release.sh"
    "${CONTAINER_RUNTIME}" exec "pulp-ephemeral" chmod a+x /root/sign_deb_release.sh
    "${CONTAINER_RUNTIME}" exec "pulp-ephemeral" bash -c "pulpcore-manager add-signing-service --class deb:AptReleaseSigningService sign_deb_release /root/sign_deb_release.sh 'Pulp QE'"
  fi
  if [ "$HAS_ANSIBLE" ]
  then
    echo "Setup ansible signing service"
    "${CONTAINER_RUNTIME}" exec -i "pulp-ephemeral" bash -c "cat > /root/sign_detached.sh" < "${BASEPATH}/../tests/assets/sign_detached.sh"
    "${CONTAINER_RUNTIME}" exec "pulp-ephemeral" chmod a+x /root/sign_detached.sh
    "${CONTAINER_RUNTIME}" exec "pulp-ephemeral" bash -c "pulpcore-manager add-signing-service --class core:AsciiArmoredDetachedSigningService sign_ansible /root/sign_detached.sh 'Pulp QE'"
  fi
fi

