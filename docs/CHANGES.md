# Changelog

[//]: # (You should *NOT* be adding new change log entries to this file, this)
[//]: # (file is managed by towncrier. You *may* edit previous change logs to)
[//]: # (fix problems like typo corrections or such.)
[//]: # (To add a new change log entry, please see)
[//]: # (https://docs.pulpproject.org/contributing/git.html#changelog-update)

[//]: # (WARNING: Don't drop the towncrier directive!)

[//]: # (towncrier release notes start)

## 0.13.0 (2021-12-16)

### Features

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
- Added `reset` command to access_policies.
  Changed `--permissions-assignment` to `--creation-hooks` to follow pulpcore 3.17 naming.
  [#438](https://github.com/pulp/pulp-cli/issues/438)
- Add a generic command group for object permission management.
  Added object permission management to tasks, groups and RBAC content guards.
  [#439](https://github.com/pulp/pulp-cli/issues/439)


### Bugfixes

- Fixed a bug where in the version lookup, where "--version 0" lead to latest.
  [#415](https://github.com/pulp/pulp-cli/issues/415)


### Improved Documentation

- Updated docs home page to reflect current plugin support of the CLI.
  [#394](https://github.com/pulp/pulp-cli/issues/394)
- Added Supported Worklows page to detail the workflows and features of the CLI.
  [#395](https://github.com/pulp/pulp-cli/issues/395)


### Translations

- Added some German translations.
  [#328](https://github.com/pulp/pulp-cli/issues/328)


---


## 0.12.0 (2021-10-06)
======================


### Features

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
- Added refresh command for pulp_file Alternate Content Sources.
  [#377](https://github.com/pulp/pulp-cli/issues/377)
- Added pulp_rpm Alternate Content Source commands.
  [#378](https://github.com/pulp/pulp-cli/issues/378)
- Added the openapi command group to debug to ease reading the schema.
  [#384](https://github.com/pulp/pulp-cli/issues/384)


### Bugfixes

- Fixed the referenced version with the `--version` parameter.
  [#351](https://github.com/pulp/pulp-cli/issues/351)
- Fixed nullable fields for rpm remote.
  [#373](https://github.com/pulp/pulp-cli/issues/373)


### Improved Documentation

- Add installation instructions for plugins and a list of known plugins.
  [#331](https://github.com/pulp/pulp-cli/issues/331)
- Moved CHANGES.md to publish them along with the documentation.
  [#336](https://github.com/pulp/pulp-cli/issues/336)
- Reformatted CHANGES with Markdown syntax.
  [#337](https://github.com/pulp/pulp-cli/issues/337)
- Add a tabular view to the global options.
  [#357](https://github.com/pulp/pulp-cli/issues/357)


### Deprecations and Removals

- Bumped required pulpcore version to >=3.11 and removed legacy workarounds.
  [#380](https://github.com/pulp/pulp-cli/issues/380)


### Misc

- [#342](https://github.com/pulp/pulp-cli/issues/342)


---


## 0.11.0 (2021-08-10)

### Features

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


### Bugfixes

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


## 0.10.1 (2021-06-30)

### Bugfixes

- Fixed a bug in the docs publishing workflow.
  [#286](https://github.com/pulp/pulp-cli/issues/286)
- Unconditionally add the fake not namespaced `pulp_cli` to the distribution on pypi to make it able to be consumed by `setuptools<40`.
  [#287](https://github.com/pulp/pulp-cli/issues/287)


---


## 0.10.0 (2021-06-30)

### Features

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


### Bugfixes

- Properly report timed out tasks.
  [#232](https://github.com/pulp/pulp-cli/issues/232)
- Use `find_packages` instead of `find_namespace_packages` in setup to be compatible with `setuptools<39.2.0`.
  [#248](https://github.com/pulp/pulp-cli/issues/248)


---


## 0.9.0 (2021-05-17)


### Features

- Disabled following of redirects and added better handling of response codes.
  [#221](https://github.com/pulp/pulp-cli/issues/221)
- Added `--force` as the inverse of `--dry-run` and started to allow `dry_run` in the settings.
  [#236](https://github.com/pulp/pulp-cli/issues/236)
- Added config validation to `config create` and `config edit`.
  [#239](https://github.com/pulp/pulp-cli/issues/239)


### Bugfixes

- Fixed extra request when using the repository version option.
  [#223](https://github.com/pulp/pulp-cli/issues/223)
- Fix requirements file option for ansible collection remote commands.
  [#226](https://github.com/pulp/pulp-cli/issues/226)
- Properly truncate file before saving settings in `config edit`.
  [#239](https://github.com/pulp/pulp-cli/issues/239)


### Misc

- [#235](https://github.com/pulp/pulp-cli/issues/235)


---


## 0.8.0 (2021-04-30)


### Features

- Added support for autopublish and autodistribute in `pulp_file` and `pulp_rpm`.
  [#155](https://github.com/pulp/pulp-cli/issues/155)
- Added a confirmation whether to continue with invalid config.
  [#156](https://github.com/pulp/pulp-cli/issues/156)
- Repository content commands are now nested under a new content subgroup.
  [#171](https://github.com/pulp/pulp-cli/issues/171)
- Added an interactive-shell mode to pulp-cli.
  [#181](https://github.com/pulp/pulp-cli/issues/181)
- Added label command to ansible distribution group.
  [#185](https://github.com/pulp/pulp-cli/issues/185)
- Added signing-service list and show commands.
  [#189](https://github.com/pulp/pulp-cli/issues/189)
- Added new python 3.2 remote options.
  [#208](https://github.com/pulp/pulp-cli/issues/208)
- Added retained_versions option to repository commands.
  [#210](https://github.com/pulp/pulp-cli/issues/210)
- Added the task-group subcommand.
  [#211](https://github.com/pulp/pulp-cli/issues/211)
- Added mirror flag support for pulp rpm repository sync.
  [#212](https://github.com/pulp/pulp-cli/issues/212)
- Added support for file paths for plan argument for miigration plan create command.
  [#213](https://github.com/pulp/pulp-cli/issues/213)


### Bugfixes

- Improved the error message, when a required server component is missing.
  [#184](https://github.com/pulp/pulp-cli/issues/184)


### Deprecations and Removals


- Repository add/remove/modify commands have now been deprecated. Please use the new content subgroup commands.
  [#215](https://github.com/pulp/pulp-cli/issues/215)


### Misc

- [#190](https://github.com/pulp/pulp-cli/issues/190)


---


## 0.7.0 (2021-03-15)


### Features

- Added the python command group.
  [#73](https:// github.com/pulp/pulp-cli/issues/73)
- Distributions can now be listed with options `--base-path` and `--base-path-contains`.
  [#134](https://github.com/pulp/pulp-cli/issues/134)
- Taught rpm/repository about the retain-package-versions attribute.
  [#172](https://github.com/pulp/pulp-cli/issues/172)
- Added the container namespace command group.
  [#176](https://github.com/pulp/pulp-cli/issues/176)


---


## 0.6.0 (2021-02-26)


### Features

- In pulpcore 3.11, the component names changed to fix a bug. This ported `pulp-cli` to use the new
  names and provides dictionary named `new_component_names_to_pre_3_11_names` in the
  `pulpcore.cli.common.context` module which provides new to old name mappings for a fallback
  support. `pulp-cli` plugins can add to this list by importing and modifying that dictionary also.
  [#153](https://github.com/pulp/pulp-cli/issues/153)


---


## 0.5.0 (2021-02-20)


### Features

- Made task state a choice option for pulp task list.
  [#115](https://github.com/pulp/pulp-cli/issues/115)
- Added support for pulp-2to3-migration.
  [#133](https://github.com/pulp/pulp-cli/issues/133)
- Added worker command.
  [#144](https://github.com/pulp/pulp-cli/issues/144)
- Added the ability to include multiple server profiles into the pulp cli config.
  [#145](https://github.com/pulp/pulp-cli/issues/145)


### Misc

- [#148](https://github.com/pulp/pulp-cli/issues/148)


---


## 0.4.0 (2021-02-10)


### Features

- Added config commands to manage pulp-cli's config.
  [#111](https://github.com/pulp/pulp-cli/issues/111)
- Added support for client certificate auth.
  [#122](https://github.com/pulp/pulp-cli/issues/122)
- Added `--href` options to address rpm resources.
  [#124](https://github.com/pulp/pulp-cli/issues/124)


### Bugfixes

- Improve handling of background option and ctrl-c with tasks.
  [#85](https://github.com/pulp/pulp-cli/issues/85)
- Added read capability to rpm remote.
  [#125](https://github.com/pulp/pulp-cli/issues/125)


### Deprecations and Removals

- Moved the location of `--repository` option after the last command for version commands.
  [#123](https://github.com/pulp/pulp-cli/issues/123)


### Misc

- [#91](https://github.com/pulp/pulp-cli/issues/91), [#118](https://github.com/pulp/pulp-cli/issues/118)


---


## 0.3.0 (2021-02-04)


### Features

- Added label commands.
  [#100](https://github.com/pulp/pulp-cli/issues/100)


### Bugfixes

- Fixed missing READ_ID error for pulp file remote show.
  [#107](https://github.com/pulp/pulp-cli/issues/107)


### Misc

- [#89](https://github.com/pulp/pulp-cli/issues/89)


---


## 0.2.0 (2021-01-26)


### Features

- Basic CRUD support for Ansible repositories
- Basic CRUD for Ansible role remotes, use `-t role` after remote to select type
- Basic CRUD for Ansible collection remotes, use `-t collection` after remote to select type
- Sync roles/collections with `pulp ansible repository sync --name {repo_name} --remote {remote_name}`
- Postponed all server calls to the point, where a command is ready to be performed.
  This allows to access all help screens even if there is no server available.
- Added subcommand to modify file repository with many content units in one command.
- Added update command for file distribution.


---


## 0.1.0 (2021-01-15)

Initial release of pulp-cli.


---
