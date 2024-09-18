#!/bin/bash

set -eu

# I ran this with:
#
# $ podman pull registry.fedoraproject.org/fedora
# $ podman run --rm --privileged --network slirp4netns -it --volume ./:/pulp-cli fedora
#
# # /pulp-cli/test_build.sh

dnf install --setopt install_weak_deps=false -y rpmdevtools rpmlint git mock

VERSION="$(rpmspec -q --qf='%{version}\n' --srpm /pulp-cli/SPECS/pulp-cli.spec)"
RELEASE="$(rpmspec -q --qf='%{release}\n' --srpm /pulp-cli/SPECS/pulp-cli.spec)"

rpmdev-setuptree

pushd /pulp-cli
git archive --format tgz --prefix "pulp-cli-${VERSION}/" -o "/root/rpmbuild/SOURCES/pulp-cli-${VERSION}.tar.gz" "${VERSION}"
popd
cp /pulp-cli/SOURCES/* /root/rpmbuild/SOURCES

rpmbuild -bs /pulp-cli/SPECS/python-pulp-glue.spec
rpmbuild -bs /pulp-cli/SPECS/pulp-cli.spec

pushd /root/rpmbuild
mock --isolation=simple --chain -r fedora-40-x86_64 --localrepo . "SRPMS/python-pulp-glue-${VERSION}-${RELEASE}.src.rpm" "SRPMS/pulp-cli-${VERSION}-${RELEASE}.src.rpm"
popd

dnf install --setopt install_weak_deps=false -y --repofrompath pulp-cli,/root/rpmbuild/results/fedora-40-x86_64/ --setopt=pulp-cli.gpgcheck=false pulp-cli

pulp --version
