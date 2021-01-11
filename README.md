# Pulp command line interface

This is a command line interface for Pulp 3. 

This software is in beta and future releases may include backwards incompatible changes.

## General command syntax

`pulp [<global_options>] <plugin> <resource_class> [--type <resource_type>] <action> [<action_options>]`

Global options include:

  * `--base-url`
  * `--user`
  * `--password`
  * `--config`
  * `--format`
  * `-v`/`-vv`/`-vvv`

## Installation

The pulp-cli package can be installed from a variety of sources. After installing, see the next
section on how to configure pulp-cli.

### From PyPI

```
pip install pulp-cli
```

### From a source checkout

```
git clone <your_fork_url>
cd pulp-cli
pip install -e .
```

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

### Code conventions
`pulp-cli` comes with python type annotations and black code formatting.
To verify your code please run `black`, `flake8`, `shellcheck`, and `mypy`.

### Compatibility
This cli for Pulp 3 will be versioned indedendently of any version of the server components.
It is supposed to be able to communicate with different combinations of server component versions at the same time.
So it might be needed to guard certain features / workaround by the available server plugin version.
