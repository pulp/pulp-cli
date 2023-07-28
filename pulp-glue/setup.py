from setuptools import setup

try:
    from setuptools import find_namespace_packages

    plugin_packages = find_namespace_packages(include=["pulp_glue.*"], exclude=["pulp_glue.*.*"])

except ImportError:
    # Old versions of setuptools do not provide `find_namespace_packages`
    # see https://github.com/pulp/pulp-cli/issues/248
    from setuptools import find_packages

    plugins = find_packages(where="pulp_glue")
    plugin_packages = [f"pulp_glue.{plugin}" for plugin in plugins]

long_description = ""
with open("README.md") as readme:
    for line in readme:
        long_description += line

setup(
    name="pulp-glue",
    description="Version agnostic glue library to talk to pulpcore's REST API.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Pulp Team",
    author_email="pulp-list@redhat.com",
    url="https://github.com/pulp/pulp-cli",
    version="0.19.5",
    packages=plugin_packages,
    package_data={"": ["py.typed"]},
    python_requires=">=3.6",
    install_requires=[
        "packaging",
        "setuptools",
        "requests~=2.24",
    ],
    license="GPLv2+",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: System :: Software Distribution",
        "Typing :: Typed",
    ],
)
