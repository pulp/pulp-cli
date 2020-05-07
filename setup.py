from setuptools import setup, find_namespace_packages


setup(
    name="pulp-cli",
    version="0.0.0a1.dev",
    packages=find_namespace_packages(include=["pulpcore.*"]),
    install_requires=[
        "click",
        "pulpcore-client",
    ],
    entry_points='''
        [console_scripts]
        pulp=pulpcore.cli:main
    ''',
)
