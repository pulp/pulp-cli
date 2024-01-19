# Installation

## TL;DR: Get Started Real Fast

=== "pip"

    ```bash
    pip install pulp-cli[pygments]
    pulp config create -e
    # insert your server configuration here
    pulp status
    ```

=== "pipx"

    ```bash
    pipx install pulp-cli[pygments]
    pulp config create -e
    # insert your server configuration here
    pulp status
    ```

---

The pulp-cli package can be installed from a variety of sources.
After installing, see the next section on how to [configure](configuration.md) pulp-cli.

## Using pipx

To install with `pipx` run:
```bash
pipx install pulp-cli
```

You can add optional dependencies in the usual way.
```bash
pipx install pulp-cli[pygments,shell]
```

[Additional plugins](index.md#cli-plugins) need to be injected into the apps virtual environment like this:
```bash
pipx inject pulp-cli pulp-cli-deb
```

## From PyPI using pip

!!!warning

    We highly recommend using virtual environments with pip.

To install with minimal dependencies:
```bash
pip install pulp-cli  # minimal dependencies
```

You can also include optional dependencies for [advanced features](advanced_features.md) with one of the following commands:
```bash
pip install pulp-cli[pygments]  # colorized output
pip install pulp-cli[shell]  # with interactive shell mode
```

If you want to install additional cli plugins, you can follow this example:
```bash
pip install pulp-cli-deb
```

## From a source checkout

If you intend to use unreleased features, or want to contribute to the CLI, you can install from source:
```bash
git clone git@github.com:pulp/pulp-cli.git
pip install -e ./pulp-cli -e ./pulp-cli/pulp-glue

# Optionally install plugins from source
git clone git@github.com:pulp/pulp-cli-deb.git
pip install -e ./pulp-cli-deb

git clone git@github.com:pulp/pulp-cli-maven.git
pip install -e ./pulp-cli-maven -e ./pulp-cli-maven/pulp-glue-maven
```
