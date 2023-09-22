from setuptools import setup

try:
    from setuptools import find_namespace_packages

    plugin_packages = find_namespace_packages(
        include=["pulpcore.cli.*"], exclude=["pulpcore.cli.*.*"]
    )

except ImportError:
    # Old versions of setuptools do not provide `find_namespace_packages`
    # see https://github.com/pulp/pulp-cli/issues/248
    from setuptools import find_packages

    plugins = find_packages(where="pulpcore/cli")
    plugin_packages = [f"pulpcore.cli.{plugin}" for plugin in plugins]

extra_packages = ["pulp_cli", "pytest_pulp_cli"]

plugin_entry_points = [(package.rsplit(".", 1)[-1], package) for package in plugin_packages]

long_description = ""
with open("README.md") as readme:
    for line in readme:
        long_description += line

setup(
    name="pulp-cli",
    description="Command line interface to talk to pulpcore's REST API.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Pulp Team",
    author_email="pulp-list@redhat.com",
    url="https://github.com/pulp/pulp-cli",
    version="0.20.4",
    packages=plugin_packages + extra_packages,
    package_data={"": ["py.typed", "locale/*/LC_MESSAGES/*.mo"]},
    python_requires=">=3.6",
    install_requires=[
        "pulp-glue==0.20.4",
        "click>=8.0.0,<8.1.4",
        "PyYAML>=5.3,<6.1",
        "schema>=0.7.5,<0.8",
        "toml>=0.10.2,<0.11",
    ],
    extras_require={
        "pygments": ["pygments"],
        "shell": ["click-shell~=2.1"],
    },
    entry_points={
        "console_scripts": ["pulp=pulp_cli:main"],
        "pulp_cli.plugins": [f"{name}={module}" for name, module in plugin_entry_points],
    },
    license="GPLv2+",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: System :: Software Distribution",
        "Typing :: Typed",
    ],
)
