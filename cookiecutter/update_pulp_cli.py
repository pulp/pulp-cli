#!/usr/bin/env python3

# Requirements:
# packaging
# tomlkit

import json
import logging
from packaging.version import Version
from packaging.requirements import Requirement
from packaging.specifiers import Specifier, SpecifierSet
from packaging.utils import canonicalize_name
import urllib.request

import tomlkit


WAREHOUSE = "https://pypi.org"
_logger = logging.getLogger("venia")


def strategy_semver(requirement: Requirement, latest_version: Version) -> Requirement | None:
    requirement = Requirement(str(requirement))
    upper_bound = None
    rest = []
    for spec in requirement.specifier:
        if spec.operator in {"<", "<=", "=="}:
            if upper_bound is not None:
                if Version(spec.version) > Version(upper_bound.version):
                    rest.append(upper_bound)
                    upper_bound = spec
                else:
                    rest.append(spec)
            else:
                upper_bound = spec
        else:
            rest.append(spec)
    assert upper_bound is not None
    if latest_version < Version(upper_bound.version):
        _logger.warn(
            f"Dependency on {requirement} cannot be updated to include latest version {latest_version}."
        )
    else:
        if upper_bound.operator == "==":
            upper_bound = Specifier(f"=={latest_version}")
        elif upper_bound.operator == "<=":
            upper_bound = Specifier(f"<={latest_version}")
        elif upper_bound.operator == "<":
            dots = len([c for c in upper_bound.version if c == "."])
            if dots == 0:
                new_version = f"{latest_version.major + 1}"
            elif dots == 1:
                new_version = f"{latest_version.major}.{latest_version.minor + 1}"
            elif dots == 2:
                new_version = (
                    f"{latest_version.major}.{latest_version.minor}.{latest_version.micro + 1}"
                )
            else:
                raise RuntimeError("Too many parts for a semver boundary.")
            upper_bound = Specifier(f"<{new_version}")
        requirement.specifier = SpecifierSet(",".join(map(str, [upper_bound] + rest)))
        return requirement
    return None


def latest_version(canonical_name: str, allow_prereleases: bool | None = None) -> Version:
    with urllib.request.urlopen(f"{WAREHOUSE}/pypi/{canonical_name}/json") as response:
        releases = json.loads(response.read())["releases"]
    available_versions = sorted(
        (
            version
            for version in (Version(key) for key in releases.keys())
            if allow_prereleases or not version.is_prerelease
        )
    )
    return available_versions[-1]


def main() -> None:
    pulp_cli_version = latest_version("pulp-cli")

    update = False
    new_specifier: SpecifierSet | None = None

    with open("pyproject.toml", "r") as fp:
        pyproject_toml = tomlkit.load(fp)
    glue_available = bool(pyproject_toml["tool"]["pulp_cli_template"]["app_label"])  # type: ignore
    app_label = str(pyproject_toml["tool"]["pulp_cli_template"]["app_label"])  # type: ignore

    for i, dependency in enumerate(pyproject_toml["project"]["dependencies"]):  # type: ignore
        requirement = Requirement(dependency)
        if canonicalize_name(requirement.name, validate=True) == "pulp-cli":
            if pulp_cli_version not in requirement.specifier:
                new_requirement = strategy_semver(requirement, pulp_cli_version)
                if new_requirement is not None:
                    pyproject_toml["project"]["dependencies"][i] = str(  # type:ignore
                        new_requirement
                    )
                    new_specifier = new_requirement.specifier
                    update = True
            break

    if update:
        if glue_available:
            with open(f"pulp-glue-{app_label}/pyproject.toml", "r") as fp:
                glue_pyproject_toml = tomlkit.load(fp)
            for i, dependency in enumerate(glue_pyproject_toml["project"]["dependencies"]):  # type: ignore
                requirement = Requirement(dependency)
                if canonicalize_name(requirement.name, validate=True) == "pulp-glue":
                    assert new_specifier is not None
                    requirement.specifier = new_specifier
                    glue_pyproject_toml["project"]["dependencies"][i] = str(  # type:ignore
                        requirement
                    )
            with open(f"pulp-glue-{app_label}/pyproject.toml", "w") as fp:
                tomlkit.dump(glue_pyproject_toml, fp)

        with open("pyproject.toml", "w") as fp:
            tomlkit.dump(pyproject_toml, fp)


if __name__ == "__main__":
    main()
