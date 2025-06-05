# Pulp 3 CLI Docs

This is the documentation for Pulp 3's command line interface.

Here you can find information about how to install the Pulp 3 CLI, and general usage and syntax information.

Currently `pulp-cli` supports pulpcore and 6 of Pulp's plugins: `pulp_ansible`, `pulp-certguard`, `pulp_container`, `pulp_file`, `pulp_python` and `pulp_rpm`.
See section below for information on how to extend the CLI to support other Pulp plugins.

You can find workflow examples for the Pulp 3 CLI throughout the [plugin documentation](site:help/).
For example, [synchronizing a File repository](site:/pulp_file/docs/user/guides/sync/).

Use the links on the left to navigate.

## CLI Plugins

The CLI can be extended via external plugins.
See the [installation](docs/user/guides/installation/) instructions.

Known plugins include:

| Plugin | Description | Source Repository |
| --- | --- | --- |
| `pulp-cli-deb` | Provides the `deb` subcommand group to interact with `pulp_deb`. | [`pulp/pulp-cli-deb`](https://github.com/pulp/pulp-cli-deb) |
| `pulp-cli-gem` | Provides the `gem` subcommand group to interact with `pulp_gem`. | [`pulp/pulp-cli-gem`](https://github.com/pulp/pulp-cli-gem) |
| `pulp-cli-maven` | Provides the `maven` subcommand group to interact with `pulp_maven`. | [`pulp/pulp-cli-maven`](https://github.com/pulp/pulp-cli-maven) |
| `pulp-cli-ostree` | Provides the `ostree` subcommand group to interact with `pulp_ostree`. | [`pulp/pulp-cli-ostree`](https://github.com/pulp/pulp-cli-ostree) |
