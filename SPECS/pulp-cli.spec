Name: pulp-cli
Version: 0.29.0
Release: 1%{?dist}
Summary: Command line interface to talk to the Pulp 3 REST API

License: GPL-2.0-or-later
URL: https://github.com/pulp/pulp-cli
Source: %{url}/archive/%{version}/pulp-cli-%{version}.tar.gz

BuildArch: noarch
BuildRequires: python3-devel
# BuildRequires: pyproject-rpm-macros
Recommends: python3-pygments python3-click-shell python3-secretstorage

%global _description %{expand:
pulp-cli provides the "pulp" command, able to communicate with the Pulp3 API in
a more natural way than plain http. Specifically, resources can not only be
referenced by their href, but also their natural key (e.g. name). It also
handles waiting on tasks on behalf of the user.}

%description %_description


%prep
%autosetup -p1 -n pulp-cli-%{version}


%generate_buildrequires
%pyproject_buildrequires test_requirements.txt


%build
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files pulp_cli pulpcore pytest_pulp_cli


%check
%pyproject_check_import pulp_cli
%pytest -m help_page


%files -n pulp-cli -f %{pyproject_files}
%license LICENSE
%doc README.*
%{_bindir}/pulp


%changelog
* Tue Sep 17 2024 Matthias Dellweg <x9c4@redhat.com> - 0.29.0-1
- Bump version to 0.29.0.

* Wed Sep 11 2024 Matthias Dellweg <x9c4@redhat.com> - 0.28.3-1
- Initial specfile
