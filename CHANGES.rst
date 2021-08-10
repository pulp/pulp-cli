=========
Changelog
=========

..
    You should *NOT* be adding new change log entries to this file, this
    file is managed by towncrier. You *may* edit previous change logs to
    fix problems like typo corrections or such.
    To add a new change log entry, please see
    https://docs.pulpproject.org/contributing/git.html#changelog-update

    WARNING: Don't drop the towncrier directive!

.. towncrier release notes start

0.11.0 (2021-08-10)

Features
--------

- Added support to specify skip-types on rpm sync.
  `#225 <https://github.com/pulp/pulp-cli/issues/225>`_
- Added lookup for a global config file ``/etc/pulp/cli.toml``.
  `#290 <https://github.com/pulp/pulp-cli/issues/290>`_
- Changed default config location to ``<app-dir>/cli.toml``. The old file will still be read.
  `#293 <https://github.com/pulp/pulp-cli/issues/293>`_
- Enable exports for ansible repositories.
  `#302 <https://github.com/pulp/pulp-cli/issues/302>`_
- Added --sles-auth-token to rpm remote commands.
  `#305 <https://github.com/pulp/pulp-cli/issues/305>`_
- Added ansible content list command.
  `#327 <https://github.com/pulp/pulp-cli/issues/327>`_


Bugfixes
--------

- Added validation to some json input parameters.
  `#255 <https://github.com/pulp/pulp-cli/issues/255>`_
- Fixed a bug in the docs publishing workflow.
  `#286 <https://github.com/pulp/pulp-cli/issues/286>`_
- Unconditionally add the fake not namespaced pulp_cli to the distribution on pypi to make it able to be consumed by setuptools<40.
  `#287 <https://github.com/pulp/pulp-cli/issues/287>`_
- Deprecate orphans delete command in favor of orphan cleanup and use new rest interface on pulpcore>=3.14.
  `#297 <https://github.com/pulp/pulp-cli/issues/297>`_
- Changed the name of retained-versions to retain-repo-versions.
  `#298 <https://github.com/pulp/pulp-cli/issues/298>`_
- Improved a confusing error message around pulp components.
  `#299 <https://github.com/pulp/pulp-cli/issues/299>`_
- Added minimum of 1 to `--limit` option.
  `#311 <https://github.com/pulp/pulp-cli/issues/311>`_


----


0.10.1 (2021-06-30)

Bugfixes
--------

- Fixed a bug in the docs publishing workflow.
  `#286 <https://github.com/pulp/pulp-cli/issues/286>`_
- Unconditionally add the fake not namespaced pulp_cli to the distribution on pypi to make it able to be consumed by setuptools<40.
  `#287 <https://github.com/pulp/pulp-cli/issues/287>`_


----


0.10.0 (2021-06-30)

Features
--------

- Change resource options to accept plugin and type along with the name.
  `#158 <https://github.com/pulp/pulp-cli/issues/158>`_
- Added missing search options to publication list commands.
  `#207 <https://github.com/pulp/pulp-cli/issues/207>`_
- Add a timeout parameter to specify the duration how long to wait for background tasks.
  `#232 <https://github.com/pulp/pulp-cli/issues/232>`_
- Python remote fields --includes/--excludes can now be specified with requirements.txt files
  `#240 <https://github.com/pulp/pulp-cli/issues/240>`_
- Updated RPM commands to be compatible with new 3.13 auto-publish changes
  `#251 <https://github.com/pulp/pulp-cli/issues/251>`_
- Added generic content list command.
  `#254 <https://github.com/pulp/pulp-cli/issues/254>`_
- Update the click dependency to 8.0.1.
  `#256 <https://github.com/pulp/pulp-cli/issues/256>`_
- Added feature to bypass chunk uploading if the chunk size exceeds the file size. This speeds up the upload by about 30-40%.
  `#262 <https://github.com/pulp/pulp-cli/issues/262>`_
- Added ``--cid`` option to ``task list`` command to allow fitering by correlation id.
  `#269 <https://github.com/pulp/pulp-cli/issues/269>`_
- Added allow-uploads/block-uploads option to python distribution commands
  `#271 <https://github.com/pulp/pulp-cli/issues/271>`_


Bugfixes
--------

- Properly report timed out tasks.
  `#232 <https://github.com/pulp/pulp-cli/issues/232>`_
- Use ``find_packages`` instead of ``find_namespace_packages`` in setup to be compatible with ``setuptools<39.2.0``.
  `#248 <https://github.com/pulp/pulp-cli/issues/248>`_


----


0.9.0 (2021-05-17)
==================


Features
--------

- Disabled following of redirects and added better handling of response codes.
  `#221 <https://github.com/pulp/pulp-cli/issues/221>`_
- Added ``--force`` as the inverse of ``--dry-run`` and started to allow ``dry_run`` in the settings.
  `#236 <https://github.com/pulp/pulp-cli/issues/236>`_
- Added config validation to ``config create`` and ``config edit``.
  `#239 <https://github.com/pulp/pulp-cli/issues/239>`_


Bugfixes
--------

- Fixed extra request when using the repository version option.
  `#223 <https://github.com/pulp/pulp-cli/issues/223>`_
- Fix requirements file option for ansible collection remote commands.
  `#226 <https://github.com/pulp/pulp-cli/issues/226>`_
- Properly truncate file before saving settings in ``config edit``.
  `#239 <https://github.com/pulp/pulp-cli/issues/239>`_


Misc
----

- `#235 <https://github.com/pulp/pulp-cli/issues/235>`_


----


0.8.0 (2021-04-30)
==================


Features
--------

- Added support for autopublish and autodistribute in pulp_file and pulp_rpm.
  `#155 <https://github.com/pulp/pulp-cli/issues/155>`_
- Added a confirmation whether to continue with invalid config.
  `#156 <https://github.com/pulp/pulp-cli/issues/156>`_
- Repository content commands are now nested under a new content subgroup.
  `#171 <https://github.com/pulp/pulp-cli/issues/171>`_
- Added an interactive-shell mode to pulp-cli.
  `#181 <https://github.com/pulp/pulp-cli/issues/181>`_
- Added label command to ansible distribution group.
  `#185 <https://github.com/pulp/pulp-cli/issues/185>`_
- Added signing-service list and show commands.
  `#189 <https://github.com/pulp/pulp-cli/issues/189>`_
- Added new python 3.2 remote options.
  `#208 <https://github.com/pulp/pulp-cli/issues/208>`_
- Added retained_versions option to repository commands.
  `#210 <https://github.com/pulp/pulp-cli/issues/210>`_
- Added the task-group subcommand.
  `#211 <https://github.com/pulp/pulp-cli/issues/211>`_
- Added mirror flag support for pulp rpm repository sync.
  `#212 <https://github.com/pulp/pulp-cli/issues/212>`_
- Added support for file paths for plan argument for miigration plan create command.
  `#213 <https://github.com/pulp/pulp-cli/issues/213>`_


Bugfixes
--------

- Improved the error message, when a required server component is missing.
  `#184 <https://github.com/pulp/pulp-cli/issues/184>`_


Deprecations and Removals
-------------------------

- Repository add/remove/modify commands have now been deprecated. Please use the new content subgroup commands.
  `#215 <https://github.com/pulp/pulp-cli/issues/215>`_


Misc
----

- `#190 <https://github.com/pulp/pulp-cli/issues/190>`_


----


0.7.0 (2021-03-15)
==================


Features
--------

- Added the python command group.
  `#73 <https:// github.com/pulp/pulp-cli/issues/73>`_
- Distributions can now be listed with options --base-path and --base-path-contains
  `#134 <https://github.com/pulp/pulp-cli/issues/134>`_
- Taught rpm/repository about the retain-package-versions attribute.
  `#172 <https://github.com/pulp/pulp-cli/issues/172>`_
- Added the container namespace command group.
  `#176 <https://github.com/pulp/pulp-cli/issues/176>`_


----


0.6.0 (2021-02-26)
==================


Features
--------

- In pulpcore 3.11, the component names changed to fix a bug. This ported ``pulp-cli`` to use the new
  names and provides dictionary named ``new_component_names_to_pre_3_11_names`` in the
  ``pulpcore.cli.common.context`` module which provides new to old name mappings for a fallback
  support. ``pulp-cli`` plugins can add to this list by importing and modifying that dictionary also.
  `#153 <https://github.com/pulp/pulp-cli/issues/153>`_


----


0.5.0 (2021-02-20)
==================


Features
--------

- Made task state a choice option for pulp task list.
  `#115 <https://github.com/pulp/pulp-cli/issues/115>`_
- Added support for pulp-2to3-migration.
  `#133 <https://github.com/pulp/pulp-cli/issues/133>`_
- Added worker command.
  `#144 <https://github.com/pulp/pulp-cli/issues/144>`_
- Added the ability to include multiple server profiles into the pulp cli config.
  `#145 <https://github.com/pulp/pulp-cli/issues/145>`_


Misc
----

- `#148 <https://github.com/pulp/pulp-cli/issues/148>`_


----


0.4.0 (2021-02-10)
==================


Features
--------

- Added config commands to manage pulp-cli's config.
  `#111 <https://github.com/pulp/pulp-cli/issues/111>`_
- Added support for client certificate auth.
  `#122 <https://github.com/pulp/pulp-cli/issues/122>`_
- Added --href options to address rpm resources.
  `#124 <https://github.com/pulp/pulp-cli/issues/124>`_


Bugfixes
--------

- Improve handling of background option and ctrl-c with tasks.
  `#85 <https://github.com/pulp/pulp-cli/issues/85>`_
- Added read capability to rpm remote.
  `#125 <https://github.com/pulp/pulp-cli/issues/125>`_


Deprecations and Removals
-------------------------

- Moved the location of `--repository` option after the last command for version commands.
  `#123 <https://github.com/pulp/pulp-cli/issues/123>`_


Misc
----

- `#91 <https://github.com/pulp/pulp-cli/issues/91>`_, `#118 <https://github.com/pulp/pulp-cli/issues/118>`_


----


0.3.0 (2021-02-04)
==================


Features
--------

- Added label commands.
  `#100 <https://github.com/pulp/pulp-cli/issues/100>`_


Bugfixes
--------

- Fixed missing READ_ID error for pulp file remote show.
  `#107 <https://github.com/pulp/pulp-cli/issues/107>`_


Misc
----

- `#89 <https://github.com/pulp/pulp-cli/issues/89>`_


----


0.2.0 (2021-01-26)
==================


Features
--------

- Basic CRUD support for Ansible repositories
- Basic CRUD for Ansible role remotes, use '-t role' after remote to select type
- Basic CRUD for Ansible collection remotes, use '-t collection' after remote to select type
- Sync roles/collections with 'pulp ansible repository sync --name {repo_name} --remote {remote_name}'
- Postponed all server calls to the point, where a command is ready to be performed.
  This allows to access all help screens even if there is no server available.
- Added subcommand to modify file repository with many content units in one command.
- Added update command for file distribution.


----


0.1.0 (2021-01-15)
==================

Initial release of pulp-cli.


----
