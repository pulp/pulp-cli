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

## Quick start

To install and use the CLI, run these commands:

```
pip install pulp-cli[pygments]
pulp config create -e
```

Read [the installation and configuration doc](docs/install.md) for more information.

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

To learn about the structure of a command, you can use the `--help` option with any (in-)complete command.

## Shell Completion

The CLI uses the click package which supports shell completion.
To configure this, check out [click's
documentation](https://click.palletsprojects.com/en/7.x/bashcomplete/).
As an example, here is what to add to your `~/.bashrc` file if you're using bash:

```bash
eval "$(_PULP_COMPLETE=source_bash pulp)"
```

## Contributing

### Pulp CLI feedback & thank you

If you take the time to evaluate, test, or build your own CLI commands, please complete [this survey](https://forms.gle/ca1nxVVkNivEeE5m8), and we will gladly ship you some SWAG!

### Code conventions
`pulp-cli` comes with python type annotations and black code formatting.
To run the auto-formatting features, execute `make black`.
Please run `make lint` before committing changes to check for compliance.
Also please follow [The seven rules of a great Git commit message](https://chris.beams.io/posts/git-commit/).

### Global help accessibility
In order to be able to access every (sub-)commands help page,
it is necessary that no code outside of the final performing command callback accesses the `api` property of the `PulpContext`.
There are some facilities that perform lazy loading to help with that requirement.
Those include:
  - `PulpContext.api`: When accessed, the `api.json` file for the addressed server will be read or downloaded and processed. Scheduled version checks will be reevaluated.
  - `PulpContext.needs_version`: This function can be used at any time to declear that a the operation needs a plugin in a version range. The actual check will be performed, once `api` was accessed for the first time, or immediately afterwards.
  - `PulpEntityContext.entity`: This property can be used to collect lookup attributes for entities by assigining dicts to it. On read access, the entity lookup will be performed though the `api` property.
  - `PulpEntityContext.pulp_href`: This property can be used to specify an entity by its URI. It will be fetched from the server only at read access.

### Compatibility to pulp versions
This cli for Pulp 3 will be versioned independently of any version of the server components.
It is supposed to be able to communicate with different combinations of server component versions at the same time.
So it might be needed to guard certain features / workarounds by the available server plugin version.
To divert code paths depending on plugin versions, use the `PulpContext.has_version` function.
As a rule of thumb, all necessary workarounds should be implemented in the corresponding `Context` objects to provide a consistent interface to the command callbacks.

### Testing

Tests are shell scripts in `tests/scripts` with names like `test_*.sh`.
They should should focus on the cli operation and are not a replacement for pulp integration tests;
i.e. make sure the cli translates to the right api calls, but do not care about pulp internals.

#### Running Tests

In order to run tests, a running instance of pulp with all necessary plugins installed must be
configured in `tests/settings.toml`.

To run tests:

```
make test                           # all tests
pytest -m pulp_file                 # tests for pulp_file
pytest -m pulp_file -k test_remote  # run tests/scripts/pulp_file/test_remote.sh
```

## Releasing (for internal use)

1. Generate the changelog (eg `towncrier --yes --version 0.1.0`) and commit
1. Run `bumpversion release`, commit your local changes, and note the commit sha
1. Run `bumpversion minor` to update the version to the next dev release version
1. Push your commits, open a PR, and get it merged
1. After your PR is merged, pull the latest changes from develop
1. Now tag your release commit (e.g. `git tag 0.1.0`) and push to pulp/pulp-cli
1. Monitor the build job and then check PyPI to make sure the package has been uploaded
1. Send an email to pulp-list and pulp-dev to announce the release
