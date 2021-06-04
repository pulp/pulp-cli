# Releasing (for internal use)

1. Generate the changelog (eg `towncrier --yes --version 0.1.0`) and commit
1. Run `bumpversion release`, commit your local changes, and note the commit sha
1. Run `bumpversion minor` to update the version to the next dev release version
1. Push your commits, open a PR, and get it merged
1. After your PR is merged, pull the latest changes from develop
1. Now tag your release commit (e.g. `git tag 0.1.0`) and push to pulp/pulp-cli
1. Monitor the build job and then check PyPI to make sure the package has been uploaded and the docs updated
1. Send an email to pulp-list and pulp-dev to announce the release
