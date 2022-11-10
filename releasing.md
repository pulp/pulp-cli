# Releasing (for internal use)

1. Run `bumpversion release`.
1. Generate the changelog (`towncrier --yes`).
1. Check and fix the changelog according to markdown formatting and language conventions.
1. Commit your local changes with commit message "Release 0.1.0".
1. Run `bumpversion minor` to update the version to the next dev release version and commit with "Bump version to 0.2.0.dev".
1. Push your commits, open a PR, and get it merged.
1. After your PR is merged, pull the latest changes from develop.
1. Now tag your release commit (e.g. `git tag -s 0.1.0`) and push to pulp/pulp-cli.
1. Monitor the build job and then check PyPI to make sure the package has been uploaded and the docs updated.
1. Announce the release at https://discourse.pulpproject.org/c/announcements/6.
1. Go to https://github.com/pulp/pulp-cli/milestones, close out the milestone and create a new one.
