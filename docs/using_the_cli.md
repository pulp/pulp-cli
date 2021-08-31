# Using the CLI

## General command syntax

`pulp [<global_options>] <plugin> <resource_class> [--type <resource_type>] <action> [<action_options>]`

## Global options

  * `--base-url`
  * `--user`
  * `--password`
  * `--config`
  * `--profile`
  * `--format`
  * `-v`/`-vv`/`-vvv`

## Example commands

`pulp status`

`pulp file repository list`

`pulp file repository create --name file_repo1`

`pulp file repository update --name file_repo1 --description "Contains plain files"`

`pulp file repository destroy --name file_repo1`

To learn about the structure of a command, you can use the `--help` option with any (in-)complete command.
