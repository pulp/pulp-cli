# Configure (basic)

The CLI can be configured by using a toml file.
By default the location of this file is `~/.config/pulp/cli.toml`.
However, this can be customized by using the `--config` option.
Any settings supplied as options to a command will override these settings.

Example file:

```
[cli]
base_url = "https://pulp.dev"
verify_ssl = false
format = "json"
```

## Config Profiles

The CLI allows you to configure additional profiles at the same time.
If you add a `[cli-server1]` section to your config,
you can use that set of settings by specifying the `--profile server1` on the pulp command line.
This can be helpful if you need to use different usernames for certain actions,
or if you need to interact with several different Pulp servers.

## Generating a new configuration

To generate a new configuration:

```
pulp config create --base-url "http://localhost"
pulp config create -e  # with an editor (e.g. vim)
pulp config create -i  # interactive prompts
```

## Validating the configuration

The easiest way to validate your config is to call a command that interacts with your Pulp server:

```
pulp status
```

To statically validate your config file (check that it exists, that it has not erroneous values,
etc) use the validate command:

```
pulp config validate
pulp config validate --strict  # validates that all settings are present
```

## Using netrc

If no user/pass is supplied either in the config file or as an option,
then the CLI will attempt to use `~/.netrc`.
Here is a `.netrc` example for localhost:

```
machine localhost
login admin
password password
```

## Tips for Katello Users

If you have a Katello environment and wish to use pulp-cli to connect to Pulp, you'll need to
configure client certificate authentication in your `~/.config/pulp/cli.toml`:

```toml
[cli]
base_url = "https://<your FQDN>"
cert = "/etc/pki/katello/certs/pulp-client.crt"
key = "/etc/pki/katello/private/pulp-client.key"
```

Katello content-proxy servers do not possess the certificates required to communicate with Pulp;
therefore you should install pulp-cli only on the primary server, and override the `base_url` setting on the command line when you need to connect to Pulp running on a content-proxy rather than Pulp on the primary Katello server: `--base-url https://capsule.example.com`
It can be helpful to use the `--profile` option here.

As Katello uses Pulp as a backend, all modifying actions in Pulp should be performed via Katello.
Therefore you are also strongly encourged to set `dry_run = true`, to prevent accidentally calling into dangerous commands.
This setting can in turn be overwritten on the command-line with the `--force` flag.
