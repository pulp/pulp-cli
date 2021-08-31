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

You can also include optional dependencies for [advanced features](../advanced_features/) with one of the following commands:
```bash
pip install pulp-cli[pygments]  # colorized output
pip install pulp-cli[shell]  # with interactive shell mode
```

## From a source checkout

If you intend to use unreleased features, or want to contribute to the CLI, you can install from source:
```bash
git clone <your_fork_url>
cd pulp-cli
pip install -e .
```
