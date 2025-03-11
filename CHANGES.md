# Changelog

[//]: # (You should *NOT* be adding new change log entries to this file, this)
[//]: # (file is managed by towncrier. You *may* edit previous change logs to)
[//]: # (fix problems like typo corrections or such.)
[//]: # (To add a new change log entry, please see)
[//]: # (https://docs.pulpproject.org/contributing/git.html#changelog-update)

[//]: # (WARNING: Don't drop the towncrier directive!)

[//]: # (towncrier release notes start)

## 0.31.1 (2025-03-10) {: #0.31.1 }



#### Bugfixes {: #0.31.1-bugfix }

- Fix a bug when header values weren't allowed to contain other than alphanumeric characters.
  Also combine the headers from setting and the commandline.
  [#1139](https://github.com/pulp/pulp-cli/issues/1139)


### Pulp GLUE {: #0.31.1-pulp-glue }


No significant changes.


---

## 0.31.0 (2025-02-25) {: #0.31.0 }



#### Bugfixes {: #0.31.0-bugfix }

- Added "--base-repository" option to modify commands to allow creating a repository version from a different repository.
  [#618](https://github.com/pulp/pulp-cli/issues/618)


#### Misc {: #0.31.0-misc }

- Changed the upper version bound of `packaging` to the last available version according to CalVer.
  [#1125](https://github.com/pulp/pulp-cli/issues/1125)


### Pulp GLUE {: #0.31.0-pulp-glue }


#### Features {: #0.31.0-pulp-glue-feature }

- Improved validation to consume openapi 3.1 schemata also.


#### Bugfixes {: #0.31.0-pulp-glue-bugfix }

- Fixed validation failure with `additionalProperties`.


#### Misc {: #0.31.0-pulp-glue-misc }

- Changed the upper version bound of `packaging` to the last available version according to CalVer.
  [#1125](https://github.com/pulp/pulp-cli/issues/1125)


---

## 0.30.2 (2025-01-20) {: #0.30.2 }



No significant changes.


### Pulp GLUE {: #0.30.2-pulp-glue }


No significant changes.


---

## 0.30.1 (2025-01-20) {: #0.30.1 }



No significant changes.


### Pulp GLUE {: #0.30.1-pulp-glue }


No significant changes.


---

## 0.30.0 (2025-01-15) {: #0.30.0 }



#### Features {: #0.30.0-feature }

- Added `--file-url` option to file, python and rpm content create commands.
  [#file_url](https://github.com/pulp/pulp-cli/issues/file_url)


#### Bugfixes {: #0.30.0-bugfix }

- Fixed OAuth2 not using the provided CA bundle.
  [#1096](https://github.com/pulp/pulp-cli/issues/1096)
- Fixed the error message for `pulp config edit` to properly hint at `pulp config create`.


#### Improved Documentation {: #0.30.0-doc }

- Fixed formatting and removed a confusing part of advanced features.


#### Deprecations and Removals {: #0.30.0-removal }

- Drop support for the now unsupported Python version 3.8.


#### Misc {: #0.30.0-misc }

- Replaced python-toml dependency with a delicate combination of tomllib, tomli and tomli-w.
  [#1084](https://github.com/pulp/pulp-cli/issues/1084)
- Declare compatibility with Python 3.13.


### Pulp GLUE {: #0.30.0-pulp-glue }


#### Bugfixes {: #0.30.0-pulp-glue-bugfix }

- Fixes `from_config` call that messed up the headers attribute.


#### Deprecations and Removals {: #0.30.0-pulp-glue-removal }

- Drop support for the now unsupported Python version 3.8.


#### Misc {: #0.30.0-pulp-glue-misc }

- Declare compatibility with Python 3.13.


---

## 0.29.2 (2024-09-23) {: #0.29.2 }



#### Bugfixes {: #0.29.2-bugfix }

- Fixes `from_config` call that messed up the headers attribute.


### Pulp GLUE {: #0.29.2-pulp-glue }


No significant changes.


---

## 0.29.1 (2024-09-17) {: #0.29.1 }



#### Misc {: #0.29.1-misc }

- Added experimental support for Python 3.13


### Pulp GLUE {: #0.29.1-pulp-glue }


#### Misc {: #0.29.1-pulp-glue-misc }

- Added experimental support for Python 3.13


---

## 0.29.0 (2024-09-17) {: #0.29.0 }



#### Features {: #0.29.0-feature }

- Added memoization to CLI auth provider. This helps to reuse a retrieved oauth token for the lifetime of the process.
- Changed the way OAuth2 Client Credentials are provided to give the user some choice over the authentication to use.
  The new parameters `--client-id` and `--client-secret` were added and `--username`, `--password` are now restricted to HTTP Basic.


#### Deprecations and Removals {: #0.29.0-removal }

- Removed the prompt for a username.
  Starting with this release the user needs to provide the username in the settings, or via `--username` to allow http basic auth.
  If no authentication is needed or another authentication mechanism should be used, it can be omitted.


### Pulp GLUE {: #0.29.0-pulp-glue }


#### Features {: #0.29.0-pulp-glue-feature }

- Added `from_config` constructor to `PulpContext` class.
  [#1060](https://github.com/pulp/pulp-cli/issues/1060)


#### Bugfixes {: #0.29.0-pulp-glue-bugfix }

- Fixed sending no scope instead an empty scope when using the `OAuth2ClientCredentialsAuth` authentication class.
  [#1050](https://github.com/pulp/pulp-cli/issues/1050)
- Fixed the "list" commands to show the notification about not displaying all items when it shouldn't and the other way around.
  [#1068](https://github.com/pulp/pulp-cli/issues/1068)
- Addressed some edge-case failures in the oauth2-client workflow.
- Fixed regressions in the auth selection algorithm of `AuthProviderBase`.
  In particular, proposals requiring multiple mechanisms are ignored for now instead of considering each constituent individually,
  "HTTP Bearer" and other IANA schemes are no longer interpreted as "HTTP Basic" and the empty proposal rightfully reflects no needed authentication.
- Use BasicAuth for token retrieval to comply with RFC6749.


---

## 0.28.4 (2024-09-13) {: #0.28.4 }



No significant changes.


### Pulp GLUE {: #0.28.4-pulp-glue }


#### Bugfixes {: #0.28.4-pulp-glue-bugfix }

- Fixed the "list" commands to show the notification about not displaying all items when it shouldn't and the other way around.
  [#1068](https://github.com/pulp/pulp-cli/issues/1068)


---

## 0.28.3 (2024-09-12) {: #0.28.3 }



No significant changes.


### Pulp GLUE {: #0.28.3-pulp-glue }


No significant changes.


---

## 0.28.2 (2024-09-03) {: #0.28.2 }



No significant changes.


### Pulp GLUE {: #0.28.2-pulp-glue }


#### Bugfixes {: #0.28.2-pulp-glue-bugfix }

- Fixed regressions in the auth selection algorithm of `AuthProviderBase`.
  In particular, proposals requiring multiple mechanisms are ignored for now instead of considering each constituent individually,
  "HTTP Bearer" and other IANA schemes are no longer interpreted as "HTTP Basic" and the empty proposal rightfully reflects no needed authentication.


---

## 0.28.1 (2024-08-26) {: #0.28.1 }



No significant changes.


### Pulp GLUE {: #0.28.1-pulp-glue }


#### Bugfixes {: #0.28.1-pulp-glue-bugfix }

- Addressed some edge-case failures in the oauth2-client workflow.


---

## 0.28.0 (2024-08-22) {: #0.28.0 }



#### Features {: #0.28.0-feature }

- Added the following filters to `pulp rpm content list`:
    - `--arch-contains`
    - `--arch-startswith`
    - `--name-contains`
    - `--name-startswith`
    - `--release-contains`
    - `--release-startswith`
  [#687](https://github.com/pulp/pulp-cli/issues/687)
- Added support to OAuth2 ClientCredentials grant flow as authentication method.
  This is tech preview and may change without previous warning.
  [#926](https://github.com/pulp/pulp-cli/issues/926)
- Added commands for composite and header content guards.
  [#969](https://github.com/pulp/pulp-cli/issues/969)


#### Bugfixes {: #0.28.0-bugfix }

- Fix fake mode for uploading content.


### Pulp GLUE {: #0.28.0-pulp-glue }


#### Features {: #0.28.0-pulp-glue-feature }

- Added contexts for composite and header content guards.
  [#969](https://github.com/pulp/pulp-cli/issues/969)
- Added a batched `list_iterator` added to entity context.
- Added a repository scope to `PulpContentContext` to allow to operate on "content in a repository" in a natural way.
- Allow to pass limit=0 to EntityContext.list to fetch all entities.


#### Bugfixes {: #0.28.0-pulp-glue-bugfix }

- Fixed an error where safemode wrongly complained to be in `fake_mode`.
  [#1037](https://github.com/pulp/pulp-cli/issues/1037)
- Added missing `defaults` argument to `converge`.
- Fixed a bug where `create` always returned the first entry of created resources.
  Where possible, it now compares the results with `HREF_PATTERN` to select the resource to return.
- Fixed the api spec of the RPM copy command so it does not collide with other copy implementations.


---

## 0.27.3 (2024-09-12) {: #0.27.3 }



No significant changes.


### Pulp GLUE {: #0.27.3-pulp-glue }


No significant changes.


---

## 0.27.2 (2024-08-15) {: #0.27.2 }



No significant changes.


### Pulp GLUE {: #0.27.2-pulp-glue }


#### Bugfixes {: #0.27.2-pulp-glue-bugfix }

- Fixed an error where safemode wrongly complained to be in `fake_mode`.
  [#1037](https://github.com/pulp/pulp-cli/issues/1037)


---

## 0.27.1 (2024-07-31) {: #0.27.1 }



#### Bugfixes {: #0.27.1-bugfix }

- Fix fake mode for uploading content.


### Pulp GLUE {: #0.27.1-pulp-glue }


#### Bugfixes {: #0.27.1-pulp-glue-bugfix }

- Fixed a bug where `create` always returned the first entry of created resources.
  Where possible, it now compares the results with `HREF_PATTERN` to select the resource to return.
- Fixed the api spec of the RPM copy command so it does not collide with other copy implementations.


---

## 0.27.0 (2024-07-17) {: #0.27.0 }



#### Features {: #0.27.0-feature }

- Expanded on options available to `rpm content -t package upload`.
  [#994](https://github.com/pulp/pulp-cli/issues/994)
  The user can now:
    - Upload an entire directory of RPMs.
    - Choose to have them added to their desired destination as a single new repository-version.
    - Choose to have a new Publication created at the end of the uploads.


#### Bugfixes {: #0.27.0-bugfix }

- Fixed the interactive config generation in the face of options allowing multiple values.
  [#1008](https://github.com/pulp/pulp-cli/issues/1008)


#### Improved Documentation {: #0.27.0-doc }

- Fixed some docs pages and improved the table of contents.


### Pulp GLUE {: #0.27.0-pulp-glue }


#### Features {: #0.27.0-pulp-glue-feature }

- Added `converge` to the `PulpEntityContext` to allow converging on a desired entity state.
- Implemented a `fake_mode` flag on the `PulpContext` that indicates to users of the context that modifying operations should not be carried out, but faked.
  This will imply the `safe_calls_only` flag in the `api_kwargs` that will serve as a safeguard for any POST, PUT, PATCH or DELETE that still made it through.
  A `NotImplementedFake` exception will be issued in that case.


---

## 0.26.0 (2024-07-01) {: #0.26.0 }



#### Features {: #0.26.0-feature }

- Added the "pulp rpm prune-packages" command to support new RPM feature.
  See [pulp\_rpm#2909](https://github.com/pulp/pulp_rpm/issues/2909) for details.
  [#979](https://github.com/pulp/pulp-cli/issues/979)
- Added "pulp rpm copy --config --dependency-solve" support.
  [#990](https://github.com/pulp/pulp-cli/issues/990)


#### Bugfixes {: #0.26.0-bugfix }

- Don't allow requests-2.32 due to https instability issues with that release.
  [#985](https://github.com/pulp/pulp-cli/issues/985)
- A provided "Authorization" header will no longer be overruled by other authentication mechanisms.
- Fixed "Cannot use both 'auth' and 'cert'" error when trying to use pulp-cli with cert auth.


#### Deprecations and Removals {: #0.26.0-removal }

- Deprecated `settings.toml` in favor of `cli.toml` in `$XDG_CONFIG_HOME` for settings.


#### Developer Notes {: #0.26.0-devel }

- Added `pass_view_set_context` decorator to lookup `PulpViewSetContext` objects.
- Added an automatic PR labeler for "no-issue", "no-changelog", "multi-commit", "wip" and "cherry-pick".
  It is no longer necessary to put the [noissue] tag in to commits without a link to an issue.
  Instead, the reviewer should take note of the "noissue"-label and decide whether to ask for one.


#### Misc {: #0.26.0-misc }

- [#932](https://github.com/pulp/pulp-cli/issues/932)


### Pulp GLUE {: #0.26.0-pulp-glue }


#### Bugfixes {: #0.26.0-pulp-glue-bugfix }

- Fixed the logic to use requests defaults for tls verification.


#### Deprecations and Removals {: #0.26.0-pulp-glue-removal }

- Removed unused (and undocumented) `isatty` attribute from `PulpContext`.


#### Developer Notes {: #0.26.0-pulp-glue-devel }

- Added a `PulpViewSetContext` to represent a view set not attached to a specific type of entity.
  Accordingly, `PulpEntityContext` should only be used when that API is defined by a `NamedModelViewset`.


---

## 0.25.7 (2024-06-20) {: #0.25.7 }



No significant changes.


### Pulp GLUE {: #0.25.7-pulp-glue }


No significant changes.


---

## 0.25.6 (2024-06-17) {: #0.25.6 }



No significant changes.


### Pulp GLUE {: #0.25.6-pulp-glue }


No significant changes.


---

## 0.25.5 (2024-06-12) {: #0.25.5 }



#### Bugfixes {: #0.25.5-bugfix }

- Don't allow requests-2.32 due to https instability issues with that release.
  [#985](https://github.com/pulp/pulp-cli/issues/985)


### Pulp GLUE {: #0.25.5-pulp-glue }


No significant changes.


---

## 0.25.4 (2024-06-07) {: #0.25.4 }



No significant changes.


### Pulp GLUE {: #0.25.4-pulp-glue }


No significant changes.


---

## 0.25.3 (2024-06-03) {: #0.25.3 }



#### Bugfixes {: #0.25.3-bugfix }

- Fixed "Cannot use both 'auth' and 'cert'" error when trying to use pulp-cli with cert auth.


### Pulp GLUE {: #0.25.3-pulp-glue }


No significant changes.


---

## 0.25.2 (2024-05-22) {: #0.25.2 }



No significant changes.


### Pulp GLUE {: #0.25.2-pulp-glue }


#### Bugfixes {: #0.25.2-pulp-glue-bugfix }

- Fixed the logic to use requests defaults for tls verification.


---

## 0.25.1 (2024-04-30) {: #0.25.1 }



No significant changes.


### Pulp GLUE {: #0.25.1-pulp-glue }


No significant changes.


---

## 0.25.0 (2024-04-22) {: #0.25.0 }



#### Features {: #0.25.0-feature }

- Added CLI plugin information to `pulp --version` command.
- Added `pulp debug has-cli-plugin` command.
- Added `pulp debug ipython` command to drop into a python shell.


#### Bugfixes {: #0.25.0-bugfix }

- Added validation to see if `base_url` in the config looks useful.
  [#588](https://github.com/pulp/pulp-cli/issues/588)
- Fixed an issue where passing `usename=None` in `api_kwargs` was handled different than not providing it at all.


#### Improved Documentation {: #0.25.0-doc }

- Added the structure for `https://staging-docs.pulpproject.org` and populated it with existing content.
  [#903](https://github.com/pulp/pulp-cli/issues/903)


#### Deprecations and Removals {: #0.25.0-removal }

- Removed `--min` and `--max` parameters from `pulp debug has-plugin`.
  Use `--specifier` instead.
- Removed deprecated `--fields` and `--exclude-fields` options from `pulp ansible content list` command.
  Use the `--field` and `--exclude-field` options instead.
- Removed deprecated file and python content modification commands.
  Use the `pulp {file,python} content ...` commands.


#### Developer Notes {: #0.25.0-devel }

- CLI Plugins need to provide a `mount` function. This used to be an optional requirement.
- `pulpcore.cli.common.context` and `pulpcore.cli.core.context` are no longer available as a convenience export.
- `repository_option` has been removed. Please use `repository_lookup_option` instead.


### Pulp GLUE {: #0.25.0-pulp-glue }


#### Features {: #0.25.0-pulp-glue-feature }

- Added `add_user` and `remove_user` to `PulpGroupContext`.


#### Improved Documentation {: #0.25.0-pulp-glue-doc }

- Added the structure for `https://staging-docs.pulpproject.org` and populated it with existing content.
  [#903](https://github.com/pulp/pulp-cli/issues/903)
- Improve the docs split for the pulp-glue architecture documentation.


#### Deprecations and Removals {: #0.25.0-pulp-glue-removal }

- Removed `preprocess_body` from `PulpEntityContext` in favor of `preprocess_entity`.
- Removed deprecated `registered_repository_contexts`.
  Polymorpohic entity classes register themselves to the `TYPE_REGISTRY` when providing the `PLUGIN` and `RESOURCE_TYPE` class attributes.
- Removed optional `href` parameter from many verbs on `PulpEntityContext`.
  The methods rely on the `entity` or `href` properties to be preloaded.
  e.g. `entity_ctx.update(href, body=body)` should be changed to `entity_ctx.href = href; entity_ctx.update(body=body)`.
- Removed unused `format` parameter from `PulpContext`.


---

## 0.24.3 (2024-05-22) {: #0.24.3 }



No significant changes.


### Pulp GLUE {: #0.24.3-pulp-glue }


#### Bugfixes {: #0.24.3-pulp-glue-bugfix }

- Fixed the logic to use requests defaults for tls verification.


---

## 0.24.2 (2024-05-06) {: #0.24.2 }



No significant changes.


### Pulp GLUE {: #0.24.2-pulp-glue }


No significant changes.


---

## 0.24.1 (2024-03-18) {: #0.24.1 }


#### Bugfixes {: #0.24.1-bugfix }

- Fixed an issue where passing `usename=None` in `api_kwargs` was handled different than not providing it at all.


### Pulp GLUE {: #0.24.1-pulp-glue }


No significant changes.


---

## 0.24.0 (2024-03-11) {: #0.24.0 }


#### Features {: #0.24.0-feature }

- Add `plugins` configuration option to select which plugins to load.
  [#291](https://github.com/pulp/pulp-cli/issues/291)
- Added import export support of python content.
  [#609](https://github.com/pulp/pulp-cli/issues/609)
- Added support for the dbus secret service to make use of password managers.
  [#821](https://github.com/pulp/pulp-cli/issues/821)
- Added `--header` parameter to allow passing an arbitrary number of custom headers along with every request.
  [#889](https://github.com/pulp/pulp-cli/issues/889)


#### Bugfixes {: #0.24.0-bugfix }

- User-entered order of parameters no longer matters for repository version commands.
  [#650](https://github.com/pulp/pulp-cli/issues/650)
- Fixed a regression introduced in `get_translations`.
  [#874](https://github.com/pulp/pulp-cli/issues/874)
- Fixed the distribution of extra files with the package.
  This should fix both type annotations as well as translations.


#### Improved Documentation {: #0.24.0-doc }

- Better separate the concepts of cli and glue in the architecture docs.


#### Deprecations and Removals {: #0.24.0-removal }

- Dropped support for python 3.6 and 3.7.


### Pulp GLUE {: #0.24.0-pulp-glue }


#### Features {: #0.24.0-pulp-glue-feature }

- Added `auth` to `apikwargs` so you can plug in any `requests.auth.AuthBase`.
  [#821](https://github.com/pulp/pulp-cli/issues/821)
- Added `auth_provider` to `api_kwargs` to allow flexible authentication schemes driven by the openapi3 specs.


#### Bugfixes {: #0.24.0-pulp-glue-bugfix }

- Added a missing check for uniqueness on entity lookup.
  [#894](https://github.com/pulp/pulp-cli/issues/894)
- Fixed the distribution of extra files with the package.
  This should fix both type annotations as well as translations.


#### Improved Documentation {: #0.24.0-pulp-glue-doc }

- Fixed the style to display the type of objects in the code reference docs.


#### Deprecations and Removals {: #0.24.0-pulp-glue-removal }

- Dropped support for python 3.6 and 3.7.


---

## 0.23.2 (2024-01-22) {: #0.23.2 }


#### Bugfixes {: #0.23.2-bugfix }

- Fixed a regression introduced in `get_translations`.
  [#874](https://github.com/pulp/pulp-cli/issues/874)


### Pulp GLUE {: #0.23.2-pulp-glue }


No significant changes.


---

## 0.23.1 (2024-01-18) {: #0.23.1 }


#### Bugfixes {: #0.23.1-bugfix }

- Fixed the distribution of extra files with the package.
  This should fix both type annotations as well as translations.


### Pulp GLUE {: #0.23.1-pulp-glue }


#### Bugfixes {: #0.23.1-pulp-glue-bugfix }

- Fixed the distribution of extra files with the package.
  This should fix both type annotations as well as translations.


---

## 0.23.0 (2024-01-16) {: #0.23.0 }


#### Features {: #0.23.0-feature }

- Switched the buildsystem from using `setup.py` to using `pyproject.toml`.
- Ansible Collection upload now uses the Pulp V3 API and uploading directly to a repository with `--repository`.
  [#844](https://github.com/pulp/pulp-cli/issues/844)
- Added support for `--checksum-type` option (combination of `--package-checksum-type` and `--metadata-checksum-type`) when creating rpm publications and configuring rpm repository publish settings.
  [#850](https://github.com/pulp/pulp-cli/issues/850)


#### Bugfixes {: #0.23.0-bugfix }

- Fixed a bug where the filenames on uploads were not being sent.
  [#842](https://github.com/pulp/pulp-cli/issues/842)
- Remove dependency on `pkg_resources` that failed some installations but is deprecated anyway.
  [#865](https://github.com/pulp/pulp-cli/issues/865)


#### Improved Documentation {: #0.23.0-doc }

- Improved `Developer Material/Architecture` section by adding clarification about `pulp-glue`, version guards and `pulp_option` factory.
  [#836](https://github.com/pulp/pulp-cli/issues/836)
- Clarified how to handle version specifiers when testing the CLI for unreleased plugin versions (.dev).
  [#852](https://github.com/pulp/pulp-cli/issues/852)
- Added information how to use pipx for installation.


#### Deprecations and Removals {: #0.23.0-removal }

- Marked option `--sqlite-metadata` on `pulp rpm repository update/create` unavailable for `pulp_rpm>=3.25.0`, as it was removed there.
  [#831](https://github.com/pulp/pulp-cli/issues/831)


### Pulp GLUE {: #0.23.0-pulp-glue }


#### Deprecations and Removals {: #0.23.0-pulp-glue-removal }

- Added version restriction to prevent the use of `sqlite_metadata` attribute on Repository and Publication contexts for `pulp_rpm>=3.25.0`.
  [#831](https://github.com/pulp/pulp-cli/issues/831)
- Adjusted to `pulp_rpm>=3.25` no longer allowing publishing repositories with md5, sha1, or sha224 checksums.
  [#851](https://github.com/pulp/pulp-cli/issues/851)


---


## 0.22.0 (2023-12-04) {: #0.22.0 }


#### Features {: #0.22.0-feature }

- Added the ability to reclaim disk space (cmd: 'pulp repository reclaim').
  [#620](https://github.com/pulp/pulp-cli/issues/620)
- Added ``--repo-config`` option to the rpm repository and publication.


#### Bugfixes {: #0.22.0-bugfix }

- Arguments --gpgcheck and --repo-gpgcheck in creating a rpm repository no longer fail to convert to integer.
  [#677](https://github.com/pulp/pulp-cli/issues/677)
- Fixed a crash in `pulp domain` when a default value for `--domain` was provided in the config file.
  [#769](https://github.com/pulp/pulp-cli/issues/769)
- Fixed a bug where not all commands of a command group were listed in the help and available to the auto-completion.
  [#781](https://github.com/pulp/pulp-cli/issues/781)


#### Improved Documentation {: #0.22.0-doc }

- Added a version select widget to docs.
- Added reference docs for `pulpcore.cli.common.generic`.


### Pulp GLUE {: #0.22.0-pulp-glue }


#### Features {: #0.22.0-pulp-glue-feature }

- Added 'PulpGenericRepositoryContext' class to handle repository commands not available with subtypes.
  [#620](https://github.com/pulp/pulp-cli/issues/620)
- Added ``repo_config`` option PluginRequirement checks to the ``PulpRpmRepositoryContext``and ``PulpRpmPublicationContext``.
- Added parameter `pulp_href` to `PulpRepositoryVersionContext` and `number` to `PulpRepositoryContext.get_version_context`.
- Use the labels api starting with `pulpcore` 3.34.


#### Improved Documentation {: #0.22.0-pulp-glue-doc }

- Add API reference docs for pulp-glue.
  [#808](https://github.com/pulp/pulp-cli/issues/808)


#### Translations {: #0.22.0-pulp-glue-translation }

- Added translation files machinery for pulp-glue.
  [#634](https://github.com/pulp/pulp-cli/issues/634)


---


## 0.21.4 (2023-10-02) {: #0.21.4 }


#### Improved Documentation {: #0.21.4-doc }

- Added a version select widget to docs.


### Pulp GLUE {: #0.21.4-pulp-glue }


No significant changes.


---


## 0.21.3 (2023-09-22) {: #0.21.3 }


No significant changes.


### Pulp GLUE {: #0.21.3-pulp-glue }


No significant changes.


---


## 0.21.2 (2023-08-11) {: #0.21.2 }


#### Bugfixes {: #0.21.2-bugfix }

- Fixed a crash in `pulp domain` when a default value for `--domain` was provided in the config file.
  [#769](https://github.com/pulp/pulp-cli/issues/769)


### Pulp GLUE {: #0.21.2-pulp-glue }


No significant changes.


---


## 0.21.1 (2023-08-04) {: #0.21.1 }


No significant changes.


### Pulp GLUE {: #0.21.1-pulp-glue }


No significant changes.


---


## 0.21.0 (2023-08-03) {: #0.21.0 }


#### Features {: #0.21.0-feature }

- Added `role` subcommands to `rpm` commands.
  [#630](https://github.com/pulp/pulp-cli/issues/630)
- Added `upstream-pulp` command group.
  [#699](https://github.com/pulp/pulp-cli/issues/699)


#### Bugfixes {: #0.21.0-bugfix }

- Narrow down click version given a breaking change on 8.1.4.
  [#715](https://github.com/pulp/pulp-cli/issues/715)
- Pinnend PyYAML version to fix installation issues.
  [#724](https://github.com/pulp/pulp-cli/issues/724)
- Made api-quirks idempotent to prevent them from failing once the original api is fixed.
  [#752](https://github.com/pulp/pulp-cli/issues/752)


#### Misc {: #0.21.0-misc }

- [#726](https://github.com/pulp/pulp-cli/issues/726)


### Pulp GLUE {: #0.21.0-pulp-glue }


#### Features {: #0.21.0-pulp-glue-feature }

- Added role capability to rpm contexts.
  [#630](https://github.com/pulp/pulp-cli/issues/630)
- Added decorator `api_quirk` to declare version dependent fixes to the api spec.
  [#658](https://github.com/pulp/pulp-cli/issues/658)
- Added `PulpUpstreamPulpContext`.
  [#699](https://github.com/pulp/pulp-cli/issues/699)


---


## 0.20.7 (2024-01-15) {: #0.20.7 }


### Bugfixes {: #0.20.7-bugfix }

- Fixed a crash in `pulp domain` when a default value for `--domain` was provided in the config file.
  [#769](https://github.com/pulp/pulp-cli/issues/769)


---


## 0.20.6 (2023-10-02) {: #0.20.6 }


No significant changes.


---


## 0.20.5 (2023-10-02) {: #0.20.5 }


### Improved Documentation {: #0.20.0-doc }

- Added a version select widget to docs.



---


## 0.20.4 (2023-09-22) {: #0.20.4 }


No significant changes.


---


## 0.20.3 (2023-07-28) {: #0.20.3 }


### Bugfixes {: #0.20.3-bugfix }

- Made api-quirks idempotent to prevent them from failing once the original api is fixed.
  [#752](https://github.com/pulp/pulp-cli/issues/752)


---


## 0.20.2 (2023-07-19) {: #0.20.2 }


### Bugfixes {: #0.20.2-bugfix }

- Pinnend PyYAML version to fix installation issues.
  [#724](https://github.com/pulp/pulp-cli/issues/724)


---


## 0.20.1 (2023-07-07) {: #0.20.1 }


### Bugfixes {: #0.20.1-bugfix }

- Narrow down click version given a breaking change on 8.1.4.
  [#715](https://github.com/pulp/pulp-cli/issues/715)


---


## 0.20.0 (2023-06-28) {: #0.20.0 }


### Features {: #0.20.0-feature }

- Add '--metadata-signing-service' option to rpm.
  [#605](https://github.com/pulp/pulp-cli/issues/605)
- Added `PEP-440` version specifiers to `PluginRequirement` and `pulp debug has-plugin`.
  [#681](https://github.com/pulp/pulp-cli/issues/681)
- Added `--content-guard` option to distributions.
  [#697](https://github.com/pulp/pulp-cli/issues/697)


### Bugfixes {: #0.20.0-bugfix }

- Renamed `domains` command group to `domain` to follow the cli convention.
  [#685](https://github.com/pulp/pulp-cli/issues/685)
- Fixed some tests that made assumptions that worked, but were nonetheless incorrect.
  [#692](https://github.com/pulp/pulp-cli/issues/692)


### Deprecations and Removals {: #0.20.0-removal }

- Deprecate the use of `min` and `max` in `PluginRequirement`.
  [#681](https://github.com/pulp/pulp-cli/issues/681)


---


## 0.19.5 (2023-07-28) {: #0.19.5 }


### Bugfixes {: #0.19.5-bugfix }

- Made api-quirks idempotent to prevent them from failing once the original api is fixed.
  [#752](https://github.com/pulp/pulp-cli/issues/752)


---


## 0.19.4 (2023-07-19) {: #0.19.4 }


### Bugfixes {: #0.19.4-bugfix }

- Pinnend PyYAML version to fix installation issues.
  [#724](https://github.com/pulp/pulp-cli/issues/724)


---


## 0.19.3 (2023-07-10) {: #0.19.3 }


### Bugfixes {: #0.19.3-bugfix }

- Narrow down click version given a breaking change on 8.1.4.
  [#715](https://github.com/pulp/pulp-cli/issues/715)


---


## 0.19.2 (2023-05-22) {: #0.19.2 }


### Bugfixes {: #0.19.2-bugfix }

- Fixed some tests that made assumptions that worked, but were nonetheless incorrect.
  [#692](https://github.com/pulp/pulp-cli/issues/692)


---


## 0.19.1 (2023-05-02) {: #0.19.1 }


No significant changes.


---


## 0.19.0 (2023-04-14) {: #0.19.0 }


### Features {: #0.19.0-feature }

- Added a `pulp repository version list` command. This allows to find repository versions containing content.
  [#631](https://github.com/pulp/pulp-cli/issues/631)
- Added `HREF_PATTERN` to `PulpSigningServiceContext` class.
  [#653](https://github.com/pulp/pulp-cli/issues/653)
- Added more digests lookups to artifacts
  [#662](https://github.com/pulp/pulp-cli/issues/662)
- Added support for x509 and rshm cert guards.
  [#673](https://github.com/pulp/pulp-cli/issues/673)


### Bugfixes {: #0.19.0-bugfix }

- Fixed the generic-publications command.
  [#665](https://github.com/pulp/pulp-cli/issues/665)


### Improved Documentation {: #0.19.0-doc }

- Fixed the installation from source instructions to include the glue layer.
  [#654](https://github.com/pulp/pulp-cli/issues/654)
- Added `pulp-cli-maven` to the list of known plugins.
  [#656](https://github.com/pulp/pulp-cli/issues/656)


### Deprecations and Removals {: #0.19.0-removal }

- Removed deprecated commands `pulp orphans` and `pulp debug task-summary`.
  [#670](https://github.com/pulp/pulp-cli/issues/670)


---


## 0.18.2 (2023-07-30) {: #0.18.2 }


### Bugfixes {: #0.18.2-bugfix }

- Pinnend PyYAML version to fix installation issues.
  [#724](https://github.com/pulp/pulp-cli/issues/724)
- Made api-quirks idempotent to prevent them from failing once the original api is fixed.
  [#752](https://github.com/pulp/pulp-cli/issues/752)


---


## 0.18.1 (2023-07-10) {: #0.18.1 }


### Bugfixes {: #0.18.1-bugfix }

- Narrow down click version given a breaking change on 8.1.4.
  [#715](https://github.com/pulp/pulp-cli/issues/715)


---


## 0.18.0 (2023-03-09) {: #0.18.0 }


### Features {: #0.18.0-feature }

- Added support for 3.23 multi-tenancy feature Domains.
  [#642](https://github.com/pulp/pulp-cli/issues/642)
- Added known plugin requirements to the glue library layer.
  [#645](https://github.com/pulp/pulp-cli/issues/645)


### Bugfixes {: #0.18.0-bugfix }

- Reimport some missing symbols into their old location for compatibility.
  [#635](https://github.com/pulp/pulp-cli/issues/635)
- Fixed problem where rpm-repository-sync ignored --no-optimize.
  [#648](https://github.com/pulp/pulp-cli/issues/648)


---


## 0.17.1 (2023-02-17) {: #0.17.1 }


### Bugfixes {: #0.17.1-bugfix }

- Reimport some missing symbols into their old location for compatibility.
  [#635](https://github.com/pulp/pulp-cli/issues/635)


---


## 0.17.0 (2023-02-16) {: #0.17.0 }


### Features {: #0.17.0-feature }

- Updated the `--requirements` option for ansible remotes to handle both files and strings.
  [#230](https://github.com/pulp/pulp-cli/issues/230)
- Made all commands referencing entities accept both the HREF and name of the resource via the same command option.
  For example, users can additionally use the `--repository` option in ``repository show`` commands.
  [#475](https://github.com/pulp/pulp-cli/issues/475)
- Added remove-image command to pulp_container.
  [#566](https://github.com/pulp/pulp-cli/issues/566)
- Made the context layer independent of click to allow it being used like a library.
  [#597](https://github.com/pulp/pulp-cli/issues/597)
- Exposed `treeinfo` as an option for `sync --skip-type` for RPM repositories.
  [#614](https://github.com/pulp/pulp-cli/issues/614)
- Added the `pulp task summary` command as a replacement for `pulp debug task-summary`.
  [#625](https://github.com/pulp/pulp-cli/issues/625)
- Added new client library `pulp-glue` as a spin off of the `pulp-cli`.
  [#628](https://github.com/pulp/pulp-cli/issues/628)


### Bugfixes {: #0.17.0-bugfix }

- Deprecated `--fields` and `--exclude-fields` on `pulp ansible content list` in favor of `--[exclude-]field`.
  [#602](https://github.com/pulp/pulp-cli/issues/602)


### Deprecations and Removals {: #0.17.0-removal }

- Removed `pass_*_context` helpers from context layer. They moved to generic layer in 0.15.0.
  [#597](https://github.com/pulp/pulp-cli/issues/597)
- Deprecated `pulp debug task-summary` in favor of `pulp task summary`.
  [#625](https://github.com/pulp/pulp-cli/issues/625)


### Misc {: #0.17.0-misc }

- [#558](https://github.com/pulp/pulp-cli/issues/558), [#580](https://github.com/pulp/pulp-cli/issues/580)


---


## 0.16.0 (2022-11-10) {: #0.16.0 }


### Features {: #0.16.0-feature }

- Added `--max-retries` option to remotes.
  [#227](https://github.com/pulp/pulp-cli/issues/227)
- Added the ability to set labels directly on create and update.
  [#274](https://github.com/pulp/pulp-cli/issues/274)
- Added the `--repository` parameter to some upload commands.
  [#385](https://github.com/pulp/pulp-cli/issues/385)
- Introduced the option `--wait` for the `pulp task-group show` command.
  By using this option, details of the task group will be shown only after waiting for all related tasks to finish.
  [#459](https://github.com/pulp/pulp-cli/issues/459)
- Added `--optimize` and `--sync-options` to the `rpm repository sync` subcommand.
  [#462](https://github.com/pulp/pulp-cli/issues/462)
- Added `pulp debug openapi schema` and `pulp debug openapi schema-names` to investigate reusable schemas in the api.
  Renamed the original `pulp debug openapi schema` command to `pulp debug openapi spec`.
  [#534](https://github.com/pulp/pulp-cli/issues/534)
- Added support for adjusting list output: `--ordering`, `--field`, `--exclude-field`.
  [#542](https://github.com/pulp/pulp-cli/issues/542)
- Added task filtering options.
  [#543](https://github.com/pulp/pulp-cli/issues/543)
- Added `--cid` option and started reusing a recieved correlation id in all requests made by the same command.
  [#568](https://github.com/pulp/pulp-cli/issues/568)


### Bugfixes {: #0.16.0-bugfix }

- Allowed remote timeout and rate limiting parameters to be nulled by passing `""`.
  [#227](https://github.com/pulp/pulp-cli/issues/227)
- The `openapi` layer now handles all instances of `requests.RequestException`.
  This will help to give a better error message for e.g. missing schema in the `--base-url` parameter.
  [#466](https://github.com/pulp/pulp-cli/issues/466)
- Fixed an error raised when specifying no HREF value for some of the commands.
  [#545](https://github.com/pulp/pulp-cli/issues/545)
- Fixed an assertion error when canceling tasks by state.
  [#561](https://github.com/pulp/pulp-cli/issues/561)
- Fixed ``KeyError: 'missing_field'`` error when required fields are not supplied.
  [#572](https://github.com/pulp/pulp-cli/issues/572)
- Correctly identified base_path as required when creating a Distribution.
  (affected rpm, file, and python distribution create)
  [#574](https://github.com/pulp/pulp-cli/issues/574)


### Misc {: #0.16.0-misc }

- [#569](https://github.com/pulp/pulp-cli/issues/569), [#589](https://github.com/pulp/pulp-cli/issues/589)


---


## 0.15.0 (2022-07-20) {: #0.15.0 }


### Features {: #0.15.0-feature }

- Added `pulp_container` repository list/add/remove content commands.
  [#422](https://github.com/pulp/pulp-cli/issues/422)
- Added role management commands to file commands.
  [#454](https://github.com/pulp/pulp-cli/issues/454)
- Added role management to container subcommands.
  [#468](https://github.com/pulp/pulp-cli/issues/468)
- Added support for ULN remotes.
  [#470](https://github.com/pulp/pulp-cli/issues/470)
- Added ansible signature command.
  [#481](https://github.com/pulp/pulp-cli/issues/481)
- Added ansible signature list/read/upload commands.
  [#484](https://github.com/pulp/pulp-cli/issues/484)
- The `--type` option on the repository content subgroup has moved back one spot.
  To list all the content types in a repository use the `--all-types` flag on the list command.
  [#492](https://github.com/pulp/pulp-cli/issues/492)
- Added container repository copy-tag and copy-manifest commands.
  [#497](https://github.com/pulp/pulp-cli/issues/497)
- Extended "rpm content" to cover all of the RPM content-types.
  [#505](https://github.com/pulp/pulp-cli/issues/505)
- Added commands for the redirecting content guard.
  [#512](https://github.com/pulp/pulp-cli/issues/512)
- Started using uploads directly to create file content of a bigger size with pulpcore >= 3.20.
  [#514](https://github.com/pulp/pulp-cli/issues/514)
- Added global publication list command.
  Also, added new --repository filter for publication list available for pulpcore>=3.20.
  [#515](https://github.com/pulp/pulp-cli/issues/515)
- Added global distribution list command.
  [#517](https://github.com/pulp/pulp-cli/issues/517)
- Added global remote list command.
  [#518](https://github.com/pulp/pulp-cli/issues/518)
- Added `--repository` option to ansible collection signature upload and `--gpgkey` to ansible repository.
  [#532](https://github.com/pulp/pulp-cli/issues/532)


### Bugfixes {: #0.15.0-bugfix }

- Fixed bug, where the failure to load config file due to the lack of file permissions lead to a crash.
  Now those files are simply ignored.
  [#509](https://github.com/pulp/pulp-cli/issues/509)
- Fixed the heuristics for the `PARTIAL_UPDATE_ID` workaround.
  [#529](https://github.com/pulp/pulp-cli/issues/529)
- Fixed uploading content for files smaller than the chunk size.
  [#535](https://github.com/pulp/pulp-cli/issues/535)


### Deprecations and Removals {: #0.15.0-removal }

- Marked `group permission` command unusable with pulpcore 3.20.
  [#501](https://github.com/pulp/pulp-cli/issues/501)


### Misc {: #0.15.0-misc }

- [#499](https://github.com/pulp/pulp-cli/issues/499), [#520](https://github.com/pulp/pulp-cli/issues/520)


---


## 0.14.1 (2022-07-15) {: #0.14.1 }

### Bugfixes {: #0.14.1-bugfix }

- Fixed the heuristics for the `PARTIAL_UPDATE_ID` workaround.
  [#529](https://github.com/pulp/pulp-cli/issues/529)


---


## 0.14.0 (2022-03-02) {: #0.14.0 }

### Features {: #0.14.0-feature }

- Added content list/show commands for container blob/manifest/tag content types.
  [#421](https://github.com/pulp/pulp-cli/issues/421)
- Added tag/untag commands to add and remove tags from images in container repositories.
  [#423](https://github.com/pulp/pulp-cli/issues/423)
- Added a `--task-group` filter parameter to `task list`.
  [#451](https://github.com/pulp/pulp-cli/issues/451)
- Added the `api_root` setting to allow communicating with a pulp installation on a nonstandard path.
  [#453](https://github.com/pulp/pulp-cli/issues/453)
- Allow to fetch the config profile from the environment variable `PULP_CLI_PROFILE`.
  [#463](https://github.com/pulp/pulp-cli/issues/463)


### Bugfixes {: #0.14.0-bugfix }

- Fixed missing help text on path option for ACS create commands.
  [#446](https://github.com/pulp/pulp-cli/issues/446)
- Fixed a bug in reporting the failure of a task if the reason was not an exception in the task code.
  [#464](https://github.com/pulp/pulp-cli/issues/464)
- Fix rpm distribution update command failing when trying to enable/disable auto-distribute.
  [#472](https://github.com/pulp/pulp-cli/issues/472)


### Improved Documentation {: #0.14.0-doc }

- Add default help text for options taking a generic resource argument.
  [#387](https://github.com/pulp/pulp-cli/issues/387)


### Developer Notes {: #0.14.0-devel }

- Introduced `ID_PREFIX` on `PulpEntityContext` to generate most operation ids.
  [#444](https://github.com/pulp/pulp-cli/issues/444)
- Added `needs_capability` to `EntityContext` so context member function can require capabilities.
  [#465](https://github.com/pulp/pulp-cli/issues/465)


---


## 0.13.0 (2021-12-16) {: #0.13.0 }

### Features {: #0.13.0-feature }

- Allow path to certificate bundle to be specified via `PULP_CA_BUNDLE`, `REQUESTS_CA_BUNDLE` or `CURL_CA_BUNDLE` environment variables.
  Use proxy settings from environment.
  [#95](https://github.com/pulp/pulp-cli/issues/95)
- Users can now specify --client-cert, --ca-cert, and --client-key using @filepath.
  [#220](https://github.com/pulp/pulp-cli/issues/220)
- Added facilities to create, load and distribute translations.
  [#328](https://github.com/pulp/pulp-cli/issues/328)
- Added upload and show commands for Ansible Roles and Collection-Version content
  [#362](https://github.com/pulp/pulp-cli/issues/362)
- Added content management commands for Ansible repositories
  [#363](https://github.com/pulp/pulp-cli/issues/363)
- Added commands to manage roles and their association with users and groups.
  Added commands to add and remove users.
  [#382](https://github.com/pulp/pulp-cli/issues/382)
- Added `--content-hrefs` and `--protection-time` options to orphan cleanup command.
  [#398](https://github.com/pulp/pulp-cli/issues/398)
- Added support for the comps.xml upload to the rpm plugin.
  [#406](https://github.com/pulp/pulp-cli/issues/406)
- Added remote option for Python distributions.
  [#417](https://github.com/pulp/pulp-cli/issues/417)
- Added a customized user agent to api calls.
  [#426](https://github.com/pulp/pulp-cli/issues/426)
- Added support for "tasks purge".
  [#430](https://github.com/pulp/pulp-cli/issues/430)
- Added `reset` command to access policies.
  Changed `--permissions-assignment` to `--creation-hooks` to follow pulpcore 3.17 naming.
  [#438](https://github.com/pulp/pulp-cli/issues/438)
- Add a generic command group for object permission management.
  Added object permission management to tasks, groups and RBAC content guards.
  [#439](https://github.com/pulp/pulp-cli/issues/439)


### Bugfixes {: #0.13.0-bugfix }

- Fixed a bug where in the version lookup, where "--version 0" lead to latest.
  [#415](https://github.com/pulp/pulp-cli/issues/415)


### Improved Documentation {: #0.13.0-doc }

- Updated docs home page to reflect current plugin support of the CLI.
  [#394](https://github.com/pulp/pulp-cli/issues/394)
- Added Supported Worklows page to detail the workflows and features of the CLI.
  [#395](https://github.com/pulp/pulp-cli/issues/395)


### Translations {: #0.13.0-translation }

- Added some German translations.
  [#328](https://github.com/pulp/pulp-cli/issues/328)


---


## 0.12.0 (2021-10-06) {: #0.12.0 }
======================


### Features {: #0.12.0-feature }

- Chunked artifact and content uploads now allow unit specifier in ``--chunk-size`` option
  [#260](https://github.com/pulp/pulp-cli/issues/260)
- Added rpm package content commands support.
  [#284](https://github.com/pulp/pulp-cli/issues/284)
- Added the ability to pass an href to a resource option.
  [#315](https://github.com/pulp/pulp-cli/issues/315)
- Added pulp file acs command.
  [#324](https://github.com/pulp/pulp-cli/issues/324)
- Added `--all`, `--waiting` and `--running` flags to allow bulk task cancel.
  [#330](https://github.com/pulp/pulp-cli/issues/330)
- Added commands for CRUD RBAC Content Guards.
  [#352](https://github.com/pulp/pulp-cli/issues/352)
- Added the ability to delete tasks.
  [#376](https://github.com/pulp/pulp-cli/issues/376)
- Added refresh command for pulp\_file Alternate Content Sources.
  [#377](https://github.com/pulp/pulp-cli/issues/377)
- Added pulp\_rpm Alternate Content Source commands.
  [#378](https://github.com/pulp/pulp-cli/issues/378)
- Added the openapi command group to debug to ease reading the schema.
  [#384](https://github.com/pulp/pulp-cli/issues/384)


### Bugfixes {: #0.12.0-bugfix }

- Fixed the referenced version with the `--version` parameter.
  [#351](https://github.com/pulp/pulp-cli/issues/351)
- Fixed nullable fields for rpm remote.
  [#373](https://github.com/pulp/pulp-cli/issues/373)


### Improved Documentation {: #0.12.0-doc }

- Add installation instructions for plugins and a list of known plugins.
  [#331](https://github.com/pulp/pulp-cli/issues/331)
- Moved CHANGES.md to publish them along with the documentation.
  [#336](https://github.com/pulp/pulp-cli/issues/336)
- Reformatted CHANGES with Markdown syntax.
  [#337](https://github.com/pulp/pulp-cli/issues/337)
- Add a tabular view to the global options.
  [#357](https://github.com/pulp/pulp-cli/issues/357)


### Deprecations and Removals {: #0.12.0-removal }

- Bumped required pulpcore version to >=3.11 and removed legacy workarounds.
  [#380](https://github.com/pulp/pulp-cli/issues/380)


### Misc {: #0.12.0-misc }

- [#342](https://github.com/pulp/pulp-cli/issues/342)


---


## 0.11.0 (2021-08-10) {: #0.11.0 }

### Features {: #0.11.0-feature }

- Added support to specify skip-types on rpm sync.
  [#225](https://github.com/pulp/pulp-cli/issues/225)
- Added lookup for a global config file `/etc/pulp/cli.toml`.
  [#290](https://github.com/pulp/pulp-cli/issues/290)
- Changed default config location to `<app-dir>/cli.toml`. The old file will still be read.
  [#293](https://github.com/pulp/pulp-cli/issues/293)
- Enable exports for ansible repositories.
  [#302](https://github.com/pulp/pulp-cli/issues/302)
- Added --sles-auth-token to rpm remote commands.
  [#305](https://github.com/pulp/pulp-cli/issues/305)
- Added ansible content list command.
  [#327](https://github.com/pulp/pulp-cli/issues/327)


### Bugfixes {: #0.11.0-bugfix }

- Added validation to some json input parameters.
  [#255](https://github.com/pulp/pulp-cli/issues/255)
- Fixed a bug in the docs publishing workflow.
  [#286](https://github.com/pulp/pulp-cli/issues/286)
- Unconditionally add the fake not namespaced `pulp_cli` to the distribution on pypi to make it able to be consumed by `setuptools<40`.
  [#287](https://github.com/pulp/pulp-cli/issues/287)
- Deprecate orphans delete command in favor of orphan cleanup and use new rest interface on `pulpcore>=3.14`.
  [#297](https://github.com/pulp/pulp-cli/issues/297)
- Changed the name of retained-versions to retain-repo-versions.
  [#298](https://github.com/pulp/pulp-cli/issues/298)
- Improved a confusing error message around pulp components.
  [#299](https://github.com/pulp/pulp-cli/issues/299)
- Added minimum of 1 to `--limit` option.
  [#311](https://github.com/pulp/pulp-cli/issues/311)


---


## 0.10.1 (2021-06-30) {: #0.10.1 }

### Bugfixes {: #0.10.1-bugfix }

- Fixed a bug in the docs publishing workflow.
  [#286](https://github.com/pulp/pulp-cli/issues/286)
- Unconditionally add the fake not namespaced `pulp_cli` to the distribution on pypi to make it able to be consumed by `setuptools<40`.
  [#287](https://github.com/pulp/pulp-cli/issues/287)


---


## 0.10.0 (2021-06-30) {: #0.10.0 }

### Features {: #0.10.0-feature }

- Change resource options to accept plugin and type along with the name.
  [#158](https://github.com/pulp/pulp-cli/issues/158)
- Added missing search options to publication list commands.
  [#207](https://github.com/pulp/pulp-cli/issues/207)
- Add a timeout parameter to specify the duration how long to wait for background tasks.
  [#232](https://github.com/pulp/pulp-cli/issues/232)
- Python remote fields `--includes/--excludes` can now be specified with `requirements.txt` files
  [#240](https://github.com/pulp/pulp-cli/issues/240)
- Updated RPM commands to be compatible with new 3.13 auto-publish changes
  [#251](https://github.com/pulp/pulp-cli/issues/251)
- Added generic content list command.
  [#254](https://github.com/pulp/pulp-cli/issues/254)
- Update the click dependency to 8.0.1.
  [#256](https://github.com/pulp/pulp-cli/issues/256)
- Added feature to bypass chunk uploading if the chunk size exceeds the file size. This speeds up the upload by about 30-40%.
  [#262](https://github.com/pulp/pulp-cli/issues/262)
- Added `--cid` option to `task list` command to allow fitering by correlation id.
  [#269](https://github.com/pulp/pulp-cli/issues/269)
- Added allow-uploads/block-uploads option to python distribution commands
  [#271](https://github.com/pulp/pulp-cli/issues/271)


### Bugfixes {: #0.10.0-bugfix }

- Properly report timed out tasks.
  [#232](https://github.com/pulp/pulp-cli/issues/232)
- Use `find_packages` instead of `find_namespace_packages` in setup to be compatible with `setuptools<39.2.0`.
  [#248](https://github.com/pulp/pulp-cli/issues/248)


---


## 0.9.0 (2021-05-17) {: #0.9.0 }


### Features {: #0.9.0-feature }

- Disabled following of redirects and added better handling of response codes.
  [#221](https://github.com/pulp/pulp-cli/issues/221)
- Added `--force` as the inverse of `--dry-run` and started to allow `dry_run` in the settings.
  [#236](https://github.com/pulp/pulp-cli/issues/236)
- Added config validation to `config create` and `config edit`.
  [#239](https://github.com/pulp/pulp-cli/issues/239)


### Bugfixes {: #0.9.0-bugfix }

- Fixed extra request when using the repository version option.
  [#223](https://github.com/pulp/pulp-cli/issues/223)
- Fix requirements file option for ansible collection remote commands.
  [#226](https://github.com/pulp/pulp-cli/issues/226)
- Properly truncate file before saving settings in `config edit`.
  [#239](https://github.com/pulp/pulp-cli/issues/239)


### Misc {: #0.9.0-misc }

- [#235](https://github.com/pulp/pulp-cli/issues/235)


---


## 0.8.0 (2021-04-30) {: #0.8.0 }


### Features {: #0.8.0-feature }

- Added support for autopublish and autodistribute in `pulp_file` and `pulp_rpm`.
  [#155](https://github.com/pulp/pulp-cli/issues/155)
- Added a confirmation whether to continue with invalid config.
  [#156](https://github.com/pulp/pulp-cli/issues/156)
- Repository content commands are now nested under a new content subgroup.
  [#171](https://github.com/pulp/pulp-cli/issues/171)
- Added an interactive-shell mode to pulp-cli.
  [#181](https://github.com/pulp/pulp-cli/issues/181)
- Added `label` command to ansible distribution group.
  [#185](https://github.com/pulp/pulp-cli/issues/185)
- Added `signing-service` `list` and `show` commands.
  [#189](https://github.com/pulp/pulp-cli/issues/189)
- Added new pulp python 3.2 remote options.
  [#208](https://github.com/pulp/pulp-cli/issues/208)
- Added `retained_versions` option to repository commands.
  [#210](https://github.com/pulp/pulp-cli/issues/210)
- Added the `task-group` subcommand.
  [#211](https://github.com/pulp/pulp-cli/issues/211)
- Added `mirror` flag support for pulp rpm repository sync.
  [#212](https://github.com/pulp/pulp-cli/issues/212)
- Added support for file paths for plan argument for migration plan create command.
  [#213](https://github.com/pulp/pulp-cli/issues/213)


### Bugfixes {: #0.8.0-bugfix }

- Improved the error message, when a required server component is missing.
  [#184](https://github.com/pulp/pulp-cli/issues/184)


### Deprecations and Removals {: #0.8.0-removal }


- Repository add/remove/modify commands have now been deprecated. Please use the new content subgroup commands.
  [#215](https://github.com/pulp/pulp-cli/issues/215)


### Misc {: #0.8.0-misc }

- [#190](https://github.com/pulp/pulp-cli/issues/190)


---


## 0.7.0 (2021-03-15) {: #0.7.0 }


### Features {: #0.7.0-feature }

- Added the python command group.
  [#73](https:// github.com/pulp/pulp-cli/issues/73)
- Distributions can now be listed with options `--base-path` and `--base-path-contains`.
  [#134](https://github.com/pulp/pulp-cli/issues/134)
- Taught rpm/repository about the retain-package-versions attribute.
  [#172](https://github.com/pulp/pulp-cli/issues/172)
- Added the container namespace command group.
  [#176](https://github.com/pulp/pulp-cli/issues/176)


---


## 0.6.0 (2021-02-26) {: #0.6.0 }


### Features {: #0.6.0-feature }

- In pulpcore 3.11, the component names changed to fix a bug. This ported `pulp-cli` to use the new
  names and provides dictionary named `new_component_names_to_pre_3_11_names` in the
  `pulpcore.cli.common.context` module which provides new to old name mappings for a fallback
  support. `pulp-cli` plugins can add to this list by importing and modifying that dictionary also.
  [#153](https://github.com/pulp/pulp-cli/issues/153)


---


## 0.5.0 (2021-02-20) {: #0.5.0 }


### Features {: #0.5.0-feature }

- Made task state a choice option for pulp task list.
  [#115](https://github.com/pulp/pulp-cli/issues/115)
- Added support for pulp-2to3-migration.
  [#133](https://github.com/pulp/pulp-cli/issues/133)
- Added worker command.
  [#144](https://github.com/pulp/pulp-cli/issues/144)
- Added the ability to include multiple server profiles into the pulp cli config.
  [#145](https://github.com/pulp/pulp-cli/issues/145)


### Misc {: #0.5.0-misc }

- [#148](https://github.com/pulp/pulp-cli/issues/148)


---


## 0.4.0 (2021-02-10) {: #0.4.0 }


### Features {: #0.4.0-feature }

- Added config commands to manage pulp-cli's config.
  [#111](https://github.com/pulp/pulp-cli/issues/111)
- Added support for client certificate auth.
  [#122](https://github.com/pulp/pulp-cli/issues/122)
- Added `--href` options to address rpm resources.
  [#124](https://github.com/pulp/pulp-cli/issues/124)


### Bugfixes {: #0.4.0-bugfix }

- Improve handling of background option and ctrl-c with tasks.
  [#85](https://github.com/pulp/pulp-cli/issues/85)
- Added read capability to rpm remote.
  [#125](https://github.com/pulp/pulp-cli/issues/125)


### Deprecations and Removals {: #0.4.0-removal }

- Moved the location of `--repository` option after the last command for version commands.
  [#123](https://github.com/pulp/pulp-cli/issues/123)


### Misc {: #0.4.0-misc }

- [#91](https://github.com/pulp/pulp-cli/issues/91), [#118](https://github.com/pulp/pulp-cli/issues/118)


---


## 0.3.0 (2021-02-04) {: #0.3.0 }


### Features {: #0.3.0-feature }

- Added label commands.
  [#100](https://github.com/pulp/pulp-cli/issues/100)


### Bugfixes {: #0.3.0-bugfix }

- Fixed missing `READ_ID` error for pulp file remote show.
  [#107](https://github.com/pulp/pulp-cli/issues/107)


### Misc {: #0.3.0-misc }

- [#89](https://github.com/pulp/pulp-cli/issues/89)


---


## 0.2.0 (2021-01-26) {: #0.2.0 }


### Features {: #0.2.0-feature }

- Basic CRUD support for Ansible repositories
- Basic CRUD for Ansible role remotes, use `-t role` after remote to select type
- Basic CRUD for Ansible collection remotes, use `-t collection` after remote to select type
- Sync roles/collections with `pulp ansible repository sync --name {repo_name} --remote {remote_name}`
- Postponed all server calls to the point, where a command is ready to be performed.
  This allows to access all help screens even if there is no server available.
- Added subcommand to modify file repository with many content units in one command.
- Added update command for file distribution.


---


## 0.1.0 (2021-01-15) {: #0.1.0 }

Initial release of pulp-cli.


---
