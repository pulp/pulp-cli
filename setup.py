from setuptools import setup, find_namespace_packages


packages = find_namespace_packages(include=["pulpcore.cli.*"])


setup(
    name="pulp-cli",
    description="Command line interface to talk to pulpcore's REST API.",
    version="0.1.0",
    packages=packages,
    package_data={package: ["py.typed"] for package in packages},
    python_requires=">=3.6",
    install_requires=[
        "click",
        "packaging",
        "PyYAML",
        "requests",
        "toml",
    ],
    extras_require={
        "pygments": ["pygments"],
    },
    entry_points={
        "console_scripts": "pulp=pulpcore.cli.common:main",
        "pulp_cli.plugins": [
            "core=pulpcore.cli.core",
            "file=pulpcore.cli.file",
            "container=pulpcore.cli.container",
            "rpm=pulpcore.cli.rpm",
        ],
    },
    license="GPLv2+",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: System :: Software Distribution",
        "Typing :: Typed",
    ],
)
