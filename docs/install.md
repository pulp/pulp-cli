# Installing and configuration

## Installation

The pulp-cli package can be installed from a variety of sources. After installing, see the next
section on how to configure pulp-cli.

### From PyPI

```
pip install pulp-cli[pygments]  # colorized output
pip install pulp-cli  # no color output
```

### From a source checkout

```
git clone <your_fork_url>
cd pulp-cli
pip install -e .
```

## Configuration

The CLI can be configured by using a toml file.
By default the location of this file is `~/.config/pulp/settings.toml`.
However, this can be customized by using the `--config` option.
Any settings supplied as options to a command will override these settings.

Example file:

```
[cli]
base_url = "https://pulp.dev"
verify_ssl = false
format = "json"
```

### Generate

To generate a new configuration:

```
pulp config create --base_url "http://localhost"
pulp config create -e  # with an editor (e.g. vim)
pulp config create -i  # interactive prompts
```

### Validate

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

### netrc

If no user/pass is supplied either in the config file or as an option,
then the CLI will attempt to use `~/.netrc`.
Here is a `.netrc` example for localhost:

```
machine localhost
login admin
password password
```

### Katello

If you have a Katello environment and wish to use pulp-cli to connect to Pulp, you'll need to
configure client certificate authentication:

```toml
[cli]
base_url = "https://<your FQDN>"
cert = "/etc/pki/katello/certs/pulp-client.crt"
key = "/etc/pki/katello/private/pulp-client.key"
verify_ssl = false
```

