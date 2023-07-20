# Using the CLI

## General command syntax

`pulp [<global_options>] <plugin> <resource_class> [--type <resource_type>] <action> [<action_options>]`

## Global options

Global options must be specified between `pulp` and the first subcommand.
Most of these can be represented by a corresponding configuration option.

| Option | Description | Comment |
| --- | --- | --- |
| --version | Show the version and exit. | No configuration option |
| --help | Show help message and exit. | No configuration option |
| --config PATH | Specify the path of a Pulp CLI settings file to use instead of the default location. | No configuration option |
| -p, --profile TEXT | Select a [config profile](configuration.md#config-profiles) to use. | No configuration option |
| --base-url TEXT | API base url of the pulp server. | |
| --username TEXT | Username on pulp server. | |
| --password TEXT | Password on pulp server. | |
| --cert TEXT | Path to client certificate. | |
| --key TEXT | Path to client private key. Not required if client cert contains this. | |
| --verify-ssl / --no-verify-ssl | Verify SSL connection to the pulp server. | |
| --refresh-api | Invalidate cached API docs. | No configuration option |
| --dry-run / --force | Trace commands without performing any unsafe HTTP calls. | |
| -b, --background | Start tasks in the background instead of awaiting them. | No configuration option |
| -T, --timeout INTEGER | Time to wait for background tasks, set to 0 to wait infinitely. | |
| --format [json\|yaml\|none] | Select an output format for the response. | |
| -v, --verbose | Increase verbosity to explain api calls as they are made. | Repeat up to three times. |

## Example commands

`pulp status`

`pulp file repository list`

`pulp file repository create --name file_repo1`

`pulp file repository update --name file_repo1 --description "Contains plain files"`

`pulp file repository destroy --name file_repo1`

To learn about the structure of a command, you can use the `--help` option with any (in-)complete command.
