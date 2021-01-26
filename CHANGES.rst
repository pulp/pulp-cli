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

0.2.0 (2021-01-26)
==================


Features
--------

- Basic CRUD support for Ansible repositories
  `#8079 <https://pulp.plan.io/issues/8079>`_
- Basic CRUD for Ansible role remotes, use '-t role' after remote to select type
  `#8080 <https://pulp.plan.io/issues/8080>`_
- Basic CRUD for Ansible collection remotes, use '-t collection' after remote to select type
  `#8081 <https://pulp.plan.io/issues/8081>`_
- Sync roles/collections with 'pulp ansible repository sync --name {repo_name} --remote {remote_name}'
  `#8082 <https://pulp.plan.io/issues/8082>`_
- Postponed all server calls to the point, where a command is ready to be performed.
  This allows to access all help screens even if there is no server available.
  `#8118 <https://pulp.plan.io/issues/8118>`_
- Added subcommand to modify file repository with many content units in one command.
  `#8120 <https://pulp.plan.io/issues/8120>`_
- Added update command for file distribution.
  `#8145 <https://pulp.plan.io/issues/8145>`_


----


0.1.0 (2021-01-15)
==================

Initial release of pulp-cli.


----
