# Contributing to the CLI

There are many ways to contribute to this project, and all are welcome.

## Pulp CLI feedback & thank you

If you take the time to evaluate, test, or build your own CLI commands, please complete [this survey](https://forms.gle/ca1nxVVkNivEeE5m8), and we will gladly ship you some SWAG!

## Doc contributions

If you see something wrong with the docs, we welcome [documentation PRs](https://github.com/pulp/pulp-cli).

If you are using the Pulp CLI and have written end-to-end steps for Pulp workflows, we would greatly appreciate if you would contribute docs to the relevant [plugins](https://docs.pulpproject.org/pulpcore/plugins/index.html).


## Code conventions

If you are interested in contributing code, note that we have styling and formatting
conventions for both the code and our PRs:
* `pulp-cli` utilizes python type annotations and black and isort code formatting.
  To run the auto-formatting features, execute `make black`.
* To check for compliance, please, install lint requirements and run lint checks before committing changes:
  ```
  pip install -r lint_requirements.txt
  make lint
  ```
  * This executes the following checks:
    * shellcheck
    * black
    * isort
    * flake8
    * mypy
* If your PR is in response to an open issue, add `fixes #<ISSUE-NUMBER>` as its own line
in your commit message. If you do **not** have an issue, use `[noissue]`.

!!!note

   PRs need to pass these checks before they can be merged.

Also please follow [The seven rules of a great Git commit message](https://chris.beams.io/posts/git-commit/).
And finally, for each new feature, we require corresponding tests.

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

## Testing

Tests are shell scripts in `tests/scripts` with names like `test_*.sh`.
They should should focus on the cli operation and are not a replacement for pulp integration tests;
i.e. make sure the cli translates to the right api calls, but do not care about pulp internals.

## Running Tests

In order to run tests, a running instance of pulp with all necessary plugins installed must be
configured in `tests/cli.toml`.

To run tests:

```
make test                           # all tests
pytest -m pulp_file                 # tests for pulp_file
pytest -m pulp_file -k test_remote  # run tests/scripts/pulp_file/test_remote.sh
```
