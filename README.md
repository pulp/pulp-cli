# POC: pulp command line interface

This is a _technology preview_ of the command line interface for pulp3.

## General command syntax

`pulp [<options>] <plugin> <resource_class> [--type <resource_type>] <action> [<action_specifics>]`

options include:

  * `--base-url`
  * `--user`
  * `--password`

## Known issues

  * Redirecting from `http` to `https`, as done by a typical Pulp installation,
    does not work properly with `POST` and `PUT` requests.
    Please use `https://` in the base url.
    Note that the attempt to use `http` leaks sensitive data over an unencrypted connection.

## Example commands

`pulp status`

`pulp file repository list`

`pulp file repository create --name file_repo1`

`pulp file repository update --name file_repo1 --description "Contains plain files"`

`pulp file repository destroy --name file_repo1`

## Testing

Tests are run using `pytest`.

Tests are shell scripts in `tests/scripts` with names like `test_*.sh`.
