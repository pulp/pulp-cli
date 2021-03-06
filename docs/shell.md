Starting the CLI with "pulp shell" drops you into the shell:
```
(pulp) [vagrant@pulp3 ~]$ pulp shell
Starting Pulp3 interactive shell...
pulp> help

Documented commands (type help <topic>):
========================================
access-policy  config     export    group      orphans     rpm     task
ansible        container  exporter  importer   python      show    user
artifact       debug      file      migration  repository  status  worker

Undocumented commands:
======================
exit  help  quit

pulp> status
{
    ...
}

pulp> exit
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
