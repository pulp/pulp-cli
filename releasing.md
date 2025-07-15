# Releasing (for internal use)

## Using Workflows

### Create a new Y-Release Branch

  1. Trigger the "Create Release Branch" workflow on the "main" branch.
  1. Watch for the "Bump Version" PR, verify that it deletes all the changes snippets present on the new release branch, approve and merge it.

### Release from a Release Branch

  1. Trigger the "pulp-cli Release" workflow on the corresponding release branch.
  1. Lean back and see the magic happen.
  1. Wait for the "pulp-cli Publish" workflow to succeed.
  1. Verify that a new version appeared on PyPI.
  1. Verify that the docs have been updated.
  1. [only Y-releases] Announce the release at https://discourse.pulpproject.org/c/announcements/6.
  1. Look for the "Update Changelog" PR, approve and merge it.

If some thing goes wrong look at `.ci/scripts/create_release_branch.sh` and `.ci/scripts/release.sh` and follow the intentions encoded there.
