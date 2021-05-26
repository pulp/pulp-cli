# Quickstart

## Setup

To install and use the CLI, run these commands:

```
pip install pulp-cli[pygments]
pulp config create -e
```

Read [the installation and configuration doc](install.md) for more information.

## General command syntax

`pulp [<global_options>] <plugin> <resource_class> [--type <resource_type>] <action> [<action_options>]`

Global options include:

  * `--base-url`
  * `--user`
  * `--password`
  * `--config`
  * `--format`
  * `-v`/`-vv`/`-vvv`

## Example commands

`pulp status`

`pulp file repository list`

`pulp file repository create --name file_repo1`

`pulp file repository update --name file_repo1 --description "Contains plain files"`

`pulp file repository destroy --name file_repo1`

To learn about the structure of a command, you can use the `--help` option with any (in-)complete command.

## Shell Completion

The CLI uses the click package which supports shell completion.
To configure this, check out [click's
documentation](https://click.palletsprojects.com/en/7.x/bashcomplete/).
As an example, here is what to add to your `~/.bashrc` file if you're using bash:

```bash
eval "$(_PULP_COMPLETE=source_bash pulp)"
```
