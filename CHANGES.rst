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
