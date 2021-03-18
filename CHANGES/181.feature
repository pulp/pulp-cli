Added an interactive-shell mode to pulp-cli.

Starting the CLI with just "pulp" drops you into the shell:
```
(pulp) [vagrant@pulp3 ~]$ pulp
Starting Pulp3 CLI...
pulp-cli> help

Documented commands (type help <topic>):
========================================
access-policy  config     export    group      orphans     rpm     task
ansible        container  exporter  importer   python      show    user
artifact       debug      file      migration  repository  status  worker

Undocumented commands:
======================
exit  help  quit

pulp-cli> status
{
    ...
}

pulp-cli>
(pulp) [vagrant@pulp3 ~]$
```

Issuing the command with arguments works as it does currently:
```
(pulp) [vagrant@pulp3 ~]$ pulp status
{
    ...
}
(pulp) [vagrant@pulp3 ~]$
```
