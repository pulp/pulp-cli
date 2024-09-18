Name: python-pulp-glue
Version: 0.29.1
Release: 1%{?dist}
Summary: The version agnostic Pulp 3 client library in python

License: GPL-2.0-or-later
URL: https://github.com/pulp/pulp-cli
Source: %{url}/archive/%{version}/pulp-cli-%{version}.tar.gz

BuildArch: noarch
BuildRequires: python3-devel

%global _description %{expand:
pulp-glue is a library to ease the programmatic communication with the Pulp3
API. It helps to abstract different resource types with so called contexts and
allows to build or even provides complex workflows like chunked upload or
waiting on tasks.
It is built around an openapi3 parser to provide client side validation of http
requests, while accounting for known quirks and incompatibilities between
different Pulp server component versions.}

%description %_description


%package -n python3-pulp-glue
Summary: %{summary}

%description -n python3-pulp-glue %_description


%prep
%autosetup -p1 -n pulp-cli-%{version}/pulp-glue


%generate_buildrequires
%pyproject_buildrequires


%build
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files pulp_glue


%check
%pyproject_check_import pulp_glue.common.context


%files -n python3-pulp-glue -f %{pyproject_files}
%license ../LICENSE
%doc README.*


%changelog
* Tue Sep 17 2024 Matthias Dellweg <x9c4@redhat.com> - 0.29.1-1
- new version

* Tue Sep 17 2024 Matthias Dellweg <x9c4@redhat.com> - 0.29.0-1
- Bump version to 0.29.0.

* Wed Sep 11 2024 Matthias Dellweg <x9c4@redhat.com> - 0.28.3-1
- Initial specfile
