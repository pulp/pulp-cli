# Installation

## TL;DR: Get Started Real Fast

```bash
pip install pulp-cli[pygments]
pulp config create -e
# insert your server configuration here
pulp status
```

---

The pulp-cli package can be installed from a variety of sources.
After installing, see the next section on how to configure pulp-cli.

## From PyPI

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
pip install -e ./pulp-cli -e ./pulp-cli/pulp-glue --config-settings editable_mode=compat

# Optionally install plugins from source
git clone git@github.com:pulp/pulp-cli-deb.git
pip install -e ./pulp-cli-deb --config-settings editable_mode=compat

git clone git@github.com:pulp/pulp-cli-maven.git
pip install -e ./pulp-cli-maven -e ./pulp-cli-maven/pulp-glue-maven --config-settings editable_mode=compat
```
