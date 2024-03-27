# Pulp Glue Architecture

The `pulp-glue` library is an abstraction layer that lets you perform high-level operations in pulp.
Its goal is to abstract interacting with the REST api by parsing the api docs, and waiting on tasks and task groups.
It is shipped as a separate python package to allow broad use across multiple projects, such as `pulp-squeezer` and `pulpcore`.
Pulp GLUE is developed in the pulp-cli repository mainly for the consolidated tests effort.
To this end, `pulp-glue` is the go-to place for all known version-dependent Pulp API subtleties and their corresponding fixes (see Version-dependent codepaths below).

## OpenAPI

This is the part in `pulp_glue` that uses [`requests`](https://requests.readthedocs.io/) to perform low level communication with an `OpenAPI 3` compatible server.
It is not anticipated that users of Pulp Glue need to interact with this abstraction layer.

## Contexts

Pulp Glue provides the [`PulpContext`][pulp_glue.common.context.PulpContext] encapsulating the [`OpenAPI`][pulp_glue.common.openapi.OpenAPI] object.
You can use its `call` method to interact with any operation designated by its operation id.
In addition, to perform specific operations on entities, glue ships a bunch of [`PulpEntityContext`][pulp_glue.common.context.PulpEntityContext] subclasses.

### Deferred Api and Entity lookup

There are some facilities that perform deferred loading to prevent premature http requests.
Those include:

  - `PulpContext.api`: When accessed, the `api.json` file for the addressed server will be read or downloaded and processed.
    Scheduled version checks will be evaluated at that point.
  - `PulpContext.needs_version`: This function can be used at any time to declare that an operation needs a plugin in a version range.
    The actual check will be performed immediately when `api` already was accessed, or scheduled for later.
  - `PulpEntityContext.entity`: This property can be used to collect lookup attributes for entities by assigning dicts to it.
    On read access, the entity lookup will be performed through the `api` property.
  - `PulpEntityContext.pulp_href`: This property can be used to specify an entity by its URI.
    It will be fetched from the server only at read access.

### Type Registries

For some operations, it is important to know all specialized subclasses of a Pulp Entity type.
Therefore certain general Entity types (usually denoted Master/Detail in Pulp) come with a `TYPE_REGISTRY`.

### Plugin Requirements / Version Dependant Code Paths

`PluginRequirement` is the abstracted concept of the existence or non-existence of a plugin in the target Pulp server.
A `PluginRequirement` is therefore instantiated with the `app_label` of a plugin and optionally a PEP-440 compatible version specifier set.
Additionally an `inverted` flag can be passed to assert on the absence instead of the presence.
Lastly, you can add the name of a `feature` to help build useful failure messages.

Typically, plugin requirements are checked by passing into `PulpContext.has_plugins` or `PulpContext.needs_plugin`, but can also be used indirectly by assigning to a capability.

### Capabilities

Some Entities may provide support for different Pulp concepts based on their plugins version.
e.g. `Pulp Import Export` for a specific repository type may be added in a certain Pulp Plugin version.
You can add a `capability` to the `PulpEntityContext` subclass with an attached `PluginRequirement`.
Whenever glue attempts to perform the corresonding action, the capabilities are first checked against the server's versions.

### API quirks

Sometimes, the api documentation simply does not reflect the actual api behaviour.
In these cases one can add version dependent api quirks to Pulp Glue that will be executed as a hook after fetching the api documentation.
See the `pulp_glue.common.api_quirk` decorator.

## Plugin System

Pulp Glue comes with a plugin interface to be easily extendible.
Multiple plugins can be provided by the same Python package and some plugins are shipped with the pulp-glue core package.
