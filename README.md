# POC: pulp command line interface

This is a _technology preview_ of the command line interface for pulp3.

## General command syntax

`pulp [<options>] <plugin> <resource_class> [--type <resource_type>] <action> [<action_specifics>]`

options include:

  * `--base-url`
  * `--user`
  * `--password`

## Configuration

The CLI can be configured by using a toml file.
By default the location of this file is `~/.config/pulp/settings.toml`.
However, this can be customized by using the `--config` option.
Any settings supplied as options to a command will override these settings.

Example file:

```toml
[cli]
base_url = "https://pulp.dev"
verify_ssl = false
format = "json"
```

### netrc

If no user/pass is supplied either in the config file or as an option,
then the CLI will attempt to use `~/.netrc`.
Here is a `.netrc` example for localhost:

```
machine localhost
login admin
password password
```

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

## Shell Completion

The CLI uses the click package which supports shell completion.
To configure this, check out [click's
documentation](https://click.palletsprojects.com/en/7.x/bashcomplete/).
As an example, here is what to add to your `~/.bashrc` file if you're using bash:

```bash
eval "$(_PULP_COMPLETE=source_bash pulp)"
```

## Contributing

`pulp-cli` comes with python type annotations and black code formatting.
To verify your code please run `black`, `flake8`, `shellcheck`, and `mypy`.
