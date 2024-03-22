# Configure (advanced)

## Custom CA bundle

You can specify a custom CA bundle for the connection to a Pulp server by providing a path in one of the following environment variables (ordered by precedence):
`PULP_CA_BUNDLE` ,`REQUESTS_CA_BUNDLE` `CURL_CA_BUNDLE`

## Shell Completion

The CLI uses the click package which supports shell completion.
To configure this, check out [click's documentation](https://click.palletsprojects.com/en/8.0.x/shell_completion/).
As an example, here is what to add to your `~/.bashrc` file if you're using bash:

```bash
eval "$(LC_ALL=C _PULP_COMPLETE=bash_source pulp)"
```

!!! note

    When using `click<8.0.0` the command instead reads:

    `eval "$(LC_ALL=C _PULP_COMPLETE=source_bash pulp)"`

## Interactive shell mode

* To use the shell mode, you need to install the the extra requirements tagged "shell". *

Starting the CLI with "pulp shell" drops you into the shell:
```plain
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
```plain
(pulp) [vagrant@pulp3 ~]$ pulp status
{
    ...
}
(pulp) [vagrant@pulp3 ~]$
```
