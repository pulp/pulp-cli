#!/bin/sh

set -eu

pulp --refresh-api --base-url "http://localhost:8080" ${PULP_API_ROOT:+--api-root "${PULP_API_ROOT}"} --username "admin" --password "password" debug has-plugin --name "deb" && HAS_DEB=true || HAS_DEB=""
pulp --base-url "http://localhost:8080" ${PULP_API_ROOT:+--api-root "${PULP_API_ROOT}"} --username "admin" --password "password" debug has-plugin --name "ansible" && HAS_ANSIBLE=true || HAS_ANSIBLE=""
if [ "$HAS_DEB" ] || [ "$HAS_ANSIBLE" ]
then
  echo "Setup the signing services"
  if "${CONTAINER_RUNTIME}" exec "pulp-ephemeral" id pulp
  then
    PULP_USER="pulp"
  else
    PULP_USER="root"
  fi
  "${CONTAINER_RUNTIME}" exec "pulp-ephemeral" mkdir -p /var/lib/pulp/scripts/
  # Setup key on the Pulp container
  echo "6EDF301256480B9B801EBA3D05A5E6DA269D9D98:6:" | "${CONTAINER_RUNTIME}" exec -i "pulp-ephemeral" su "${PULP_USER}" -c "gpg --import-ownertrust"
  curl -L https://github.com/pulp/pulp-fixtures/raw/master/common/GPG-PRIVATE-KEY-pulp-qe | "${CONTAINER_RUNTIME}" exec -i "pulp-ephemeral" su "${PULP_USER}" -c "gpg --import"
  if [ "$HAS_DEB" ]
  then
    echo "Setup deb release signing service"
    "${CONTAINER_RUNTIME}" exec -i "pulp-ephemeral" bash -c "cat > /var/lib/pulp/scripts/sign_deb_release.sh" < "${BASEPATH}/../tests/assets/sign_deb_release.sh"
    "${CONTAINER_RUNTIME}" exec "pulp-ephemeral" chmod a+x /var/lib/pulp/scripts/sign_deb_release.sh
    "${CONTAINER_RUNTIME}" exec "pulp-ephemeral" su "${PULP_USER}" -c "pulpcore-manager add-signing-service --class deb:AptReleaseSigningService sign_deb_release /var/lib/pulp/scripts/sign_deb_release.sh 'Pulp QE'"
  fi
  if [ "$HAS_ANSIBLE" ]
  then
    echo "Setup ansible signing service"
    "${CONTAINER_RUNTIME}" exec -i "pulp-ephemeral" bash -c "cat > /var/lib/pulp/scripts/sign_detached.sh" < "${BASEPATH}/../tests/assets/sign_detached.sh"
    "${CONTAINER_RUNTIME}" exec "pulp-ephemeral" chmod a+x /var/lib/pulp/scripts/sign_detached.sh
    "${CONTAINER_RUNTIME}" exec "pulp-ephemeral" su "${PULP_USER}" -c "pulpcore-manager add-signing-service --class core:AsciiArmoredDetachedSigningService sign_ansible /var/lib/pulp/scripts/sign_detached.sh 'Pulp QE'"
  fi
fi

