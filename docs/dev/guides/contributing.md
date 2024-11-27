# Contributing to the CLI

There are many ways to contribute to this project, and all are welcome.

## Get in Touch

If you want to connect with the Pulp community, ask some not-so-frequently-asked-questions or just leave general feedback, you can reach us in different ways summed up on [pulpproject.org](site:help/community/get-involved/).


## Doc Contributions

If you see something wrong with the docs, we welcome [documentation PRs](https://github.com/pulp/pulp-cli).

If you are using the Pulp CLI and have written end-to-end steps for Pulp workflows, we would greatly appreciate if you would contribute docs to the relevant [plugins](site:help/).


## Code Conventions

If you are interested in contributing code,
note that we have styling and formatting conventions for both the code and our PRs:

- Code formatting is done with `isort` and `black`.

- Static analysis is performed with `flake8`.

- `pulp-cli` utilizes strict python type annotations, checked with `mypy`.

- Shell scripts must pass `shellcheck`.

- If your PR is in response to an open issue, add `fixes #<ISSUE-NUMBER>` as its own line in your commit message.
  You need to add a changelog entry for it.

- If you do not have an issue, consider adding an anonymous changelog entry anyway.
  You might be asked by the reviewer to file an issue anyway.

!!!note

    PRs need to pass these checks before they can be merged.

    We recommend running these before committing:
    ```bash
    pip install -r lint_requirements.txt  # setup, needed only once
    make format  # reformatting with isort & black
    make lint  # checking with shellcheck, isort, black, flake8 and mypy
    make format lint  # both in one command
    ```

Also please follow [The seven rules of a great Git commit message](https://chris.beams.io/posts/git-commit/).
And finally, for each new feature, we require corresponding tests.

## Testing

Tests are shell scripts in `tests/scripts` with names like `test_*.sh`.
They should should focus on the cli operation and are not a replacement for pulp integration tests;
i.e. make sure the cli translates to the right api calls, but do not care about pulp internals.

## Running Tests

In order to run tests, a running instance of pulp with all necessary plugins installed must be
configured in `tests/cli.toml`.

To run tests:

```bash
make test                           # all tests
pytest -m pulp_file                 # tests for pulp_file
pytest -m pulp_file -k test_remote  # run tests/scripts/pulp_file/test_remote.sh
```
