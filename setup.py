from setuptools import setup, find_namespace_packages


setup(
    name="pulp-cli",
    description="Command line interface to talk to pulpcore's REST API.",
    version="0.0.0a1.dev",
    packages=find_namespace_packages(include=["pulpcore.*"]),
    package_data={"pulpcore.cli": ["py.typed"]},
    python_requires=">=3.6",
    install_requires=[
        "click",
        "PyYAML",
        "requests",
        "toml",
    ],
    extras_require={
        "pygments": ["pygments"],
    },
    entry_points={
        "console_scripts": "pulp=pulpcore.cli:main",
        "pulp_cli.plugins": [
            "core=pulpcore.cli.core_cli",
            "file=pulpcore.cli.file_cli",
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
