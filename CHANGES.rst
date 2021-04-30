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
