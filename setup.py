from setuptools import setup, find_namespace_packages


setup(
    name="pulp-cli",
    version="0.0.0a1.dev",
    packages=find_namespace_packages(include=["pulpcore.*"]),
    package_data={"pulpcore.cli": ["py.typed"]},
    install_requires=[
        "click",
        "PyYAML",
        "requests",
        "toml",
    ],
    entry_points={
        "console_scripts": "pulp=pulpcore.cli:main",
        "pulp_cli.plugins": [
            "core=pulpcore.cli.core_cli",
            "file=pulpcore.cli.file_cli",
            "container=pulpcore.cli.container_cli",
        ],
    },
    extras_require={
        "pygments": ["pygments"],
    },
)
