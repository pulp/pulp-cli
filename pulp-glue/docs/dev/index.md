# Welcome to Pulp Glue

## The version agnostic Pulp 3 client library in Python

Pulp Glue is developed for and with the [Pulp CLI] in a combined repository.
Therefore they share a common [changelog] and release corresponding versions.

## Versioning Policy

Pulp Glue follows semantic versioning (SemVer) compatibility.
That is, with the one known exception that a new y-version does not necessarily imply a new feature to be available.
This is a result from releasing in lock-step with `pulp-cli`.
To stay compatible we advise to define the dependency as `pulp-glue=>x1.y1.z1,<x2.y2`.
If you just want to avoid breaking changes, you can also settle on `pulp-glue=>x1.y1.z1,<x2`.

[Pulp CLI]: site:pulp-cli/
[changelog]: site:pulp-cli/changes/
