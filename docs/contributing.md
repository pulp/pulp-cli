# Contributing

## Pulp CLI feedback & thank you

If you take the time to evaluate, test, or build your own CLI commands, please complete [this survey](https://forms.gle/ca1nxVVkNivEeE5m8), and we will gladly ship you some SWAG!

## Code conventions

`pulp-cli` comes with python type annotations and black code formatting.
To run the auto-formatting features, execute `make black`.
Please run `make lint` before committing changes to check for compliance.
Also please follow [The seven rules of a great Git commit message](https://chris.beams.io/posts/git-commit/).

## Global help accessibility

In order to be able to access every (sub-)commands help page,
it is necessary that no code outside of the final performing command callback accesses the `api` property of the `PulpContext`.
There are some facilities that perform lazy loading to help with that requirement.
Those include:
  - `PulpContext.api`: When accessed, the `api.json` file for the addressed server will be read or downloaded and processed.
    Scheduled version checks will be reevaluated.
  - `PulpContext.needs_version`: This function can be used at any time to declear that an operation needs a plugin in a version range.
    The actual check will be performed, once `api` was accessed for the first time, or immediately afterwards.
  - `PulpEntityContext.entity`: This property can be used to collect lookup attributes for entities by assigining dicts to it.
    On read access, the entity lookup will be performed though the `api` property.
  - `PulpEntityContext.pulp_href`: This property can be used to specify an entity by its URI.
    It will be fetched from the server only at read access.

### Compatibility to pulp versions
This cli for Pulp 3 will be versioned independently of any version of the server components.
It is supposed to be able to communicate with different combinations of server component versions at the same time.
So it might be needed to guard certain features / workarounds by the available server plugin version.
To divert code paths depending on plugin versions, use the `PulpContext.has_version` function.
As a rule of thumb, all necessary workarounds should be implemented in the corresponding `Context` objects to provide a consistent interface to the command callbacks.

## Testing

Tests are shell scripts in `tests/scripts` with names like `test_*.sh`.
They should should focus on the cli operation and are not a replacement for pulp integration tests;
i.e. make sure the cli translates to the right api calls, but do not care about pulp internals.

### Running Tests

In order to run tests, a running instance of pulp with all necessary plugins installed must be
configured in `tests/cli.toml`.

To run tests:

```
make test                           # all tests
pytest -m pulp_file                 # tests for pulp_file
pytest -m pulp_file -k test_remote  # run tests/scripts/pulp_file/test_remote.sh
```
