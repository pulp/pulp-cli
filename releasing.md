# Releasing (for internal use)

1. Install `bumpversion` and `towncrier` into a virtualenv or select one if it exists.
1. Run `bumpversion release`.
1. Install the corresponding `pulp-glue` and `pulp-cli` modules from the source (`pip install -e . ./pulp-glue`)
1. Generate the changelog (`towncrier --yes`).
1. Check and fix the changelog according to markdown formatting, language conventions and the expected version.
1. Commit your local changes with `git add .; git commit -m "Release 0.1.0" -m "[noissue]"`.
1. Run `bumpversion minor` or `bumpversion patch` to update the version to the next dev release version and commit with "Bump version to 0.2.0.dev".
1. Push your commits, open a PR, and get it merged.
1. After your PR is merged, pull the latest changes (`git fetch --all --tags`) and update your local branches.
1. Now tag your release commit (e.g. `git tag -s 0.1.0 HEAD^`) and push the tag to `pulp/pulp-cli`.
1. Monitor the build job and then check PyPI to make sure the package has been uploaded and the docs updated.
1. [only Y-releases] Announce the release at https://discourse.pulpproject.org/c/announcements/6.
1. [only Y-releases] Go to https://github.com/pulp/pulp-cli/milestones, close out the milestone and create a new one.
