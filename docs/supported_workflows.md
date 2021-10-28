# Supported Workflows

`pulp-cli` is still in beta, so the features and workflows listed here are subject to change.
Currently `pulp-cli` supports 5 versions of `pulpcore` from 3.11-3.16 and 5 of Pulp's plugins:
`pulp_ansible`, `pulp_container`, `pulp_file`, `pulp_python` and `pulp_rpm`. Some of Pulp's other
plugins can be added to the CLI through CLI plugins, check out [CLI plugins](/#cli-plugins) for more information.

## pulpcore

Pulpcore commands require a minimum version of 3.11. Not every command is supported for all
`pulpcore` versions. Run `pulp status` to check your connection to Pulp and see currently 
installed plugins.

### Workflows

The CLI currently supports the following workflows:

* [**Uploading** Artifacts](https://docs.pulpproject.org/pulpcore/workflows/upload-publish.html)
* [**Creating, Syncing, Distributing** Content](https://docs.pulpproject.org/pulpcore/workflows/exposing-content.html)
* [**Exporting** Content](https://docs.pulpproject.org/pulpcore/workflows/import-export.html#exporting)
* [**Labeling** Resources](https://docs.pulpproject.org/pulpcore/workflows/labels.html)

### Features

The CLI currently supports the following operations on these `pulpcore` objects
(C = Create, R = Read, U = Update, D = Delete):

* Access Policies - **RU**
* Artifacts - **CR**
* RBAC Content Guards - **CRUD, Assign, Remove**
* Exports Pulp - **CRD**
* Groups - **CRD, Add Permissions, Remove Permissions, Add Users, Remove Users**
* Signing Services - **R**
* Tasks - **RD, Cancel**
* Users - **R**


## pulp_ansible

Ansible commands require minimum version of 0.7.0. The commands can be found under the `ansible`
subgroup.

### Workflows

The CLI currently supports the following workflows:

* [**Sync/Upload/Distribute** Role Content](https://docs.pulpproject.org/pulp_ansible/workflows/roles.html)
* [**Sync/Upload/Distribute** Collection Content](https://docs.pulpproject.org/pulp_ansible/workflows/collections.html)

### Features

The CLI currently supports the following operations on these `pulp_ansible` objects
(C = Create, R = Read, U = Update, D = Delete):

* Role/Collection Version Content - **CR**
* Ansible Distributions - **CRUD**
* Role/Collection Version Remotes - **CRUD**
* Ansible Repositories - **CRUD, Modify, Sync**


## pulp_container

Container commands require `pulp_container` minimum version of 2.3.0. The commands can be found
under the `container` subgroup.

### Workflows

The CLI currently supports the following workflows:

* [**Sync** Container Images](https://docs.pulpproject.org/pulp_container/workflows/sync.html)
* [**Distribute** Container Images](https://docs.pulpproject.org/pulp_container/workflows/host.html)

### Features

The CLI currently supports the following operations on these `pulp_container` objects
(C = Create, R = Read, U = Update, D = Delete):

* Container Namespaces - **CRD**
* Container Distributions - **CRUD**
* Container Remotes - **CRUD**
* Container Repositories - **CRUD, Sync**
* Push Repositories - **RU**


## pulp_file

File commands require `pulp_file` minimum version of 1.6.0. The commands can be found under the `file`
subgroup.

### Workflows

The CLI currently supports the following workflows:

* [**Sync** File Content](https://docs.pulpproject.org/pulp_file/workflows/sync.html)
* [**Upload** File Content](https://docs.pulpproject.org/pulp_file/workflows/upload.html)
* [**Distribute** File Content](https://docs.pulpproject.org/pulp_file/workflows/publish-host.html)
* [Alternative Content Sources](https://docs.pulpproject.org/pulp_file/workflows/alternate-content-source.html)

### Features

The CLI currently supports the following operations on these `pulp_file` objects
(C = Create, R = Read, U = Update, D = Delete):

* File Alternative Content Sources - **CRUD, Add, Remove, Refresh**
* File Content - **CR**
* File Distributions - **CRUD**
* File Publications - **CRD**
* File Remotes - **CRUD**
* File Repositories - **CRUD, Modify, Sync**


## pulp_python

Python commands require `pulp_python` minimum version of 3.1.0. The commands can be found under the `python`
subgroup.

### Workflows

The CLI currently supports the following workflows:

* [**Sync** Python Packages](https://docs.pulpproject.org/pulp_python/workflows/sync.html)
* [**Upload** Python Packages](https://docs.pulpproject.org/pulp_python/workflows/upload.html)
* [**Distribute** Python Packages](https://docs.pulpproject.org/pulp_python/workflows/publish.html)

### Features

The CLI currently supports the following operations on these `pulp_python` objects
(C = Create, R = Read, U = Update, D = Delete):

* Python Package Content - **CR**
* Python Distributions - **CRUD**
* Python Publications - **CRD**
* Python Remotes - **CRUD**
* Python Repositories - **CRUD, Modify, Sync**


## pulp_rpm

Python commands require `pulp_rpm` minimum version of 3.9.0. The commands can be found under the `rpm`
subgroup.

### Workflows

The CLI currently supports the following workflows:

* [**Sync and Distribute** RPM Packages](https://docs.pulpproject.org/pulp_rpm/workflows/create_sync_publish.html)
* [**Upload** RPM Packages](https://docs.pulpproject.org/pulp_rpm/workflows/upload.html)

### Features

The CLI currently supports the following operations on these `pulp_rpm` objects
(C = Create, R = Read, U = Update, D = Delete):

* RPM Alternative Content Sources - **CRUD, Add, Remove, Refresh**
* RPM Packages Content - **CR**
* RPM Distributions - **CRUD**
* RPM Publications - **CRD**
* RPM Remote - **CRUD**
* RPM Repository - **CRUD, Modify, Sync**

