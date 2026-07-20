import datetime
import hashlib
import sys
import typing as t
from pathlib import Path

from pulp_glue.common.context import (
    EntityDefinition,
    PluginRequirement,
    PulpContentGuardContext,
    PulpContext,
    PulpEntityContext,
    PulpViewSetContext,
    preprocess_payload,
)
from pulp_glue.common.exceptions import PulpException
from pulp_glue.common.i18n import get_translation

translation = get_translation(__package__)
_ = translation.gettext


class PulpAccessPolicyContext(PulpEntityContext):
    ENTITY = _("access policy")
    ENTITIES = _("access policies")
    HREF = "access_policy_href"
    ID_PREFIX = "access_policies"

    def reset(self) -> t.Any:
        return self.call("reset", parameters={self.HREF: self.pulp_href})


class PulpArtifactContext(PulpEntityContext):
    ENTITY = _("artifact")
    ENTITIES = _("artifacts")
    HREF = "artifact_href"
    PLUGIN = "core"
    MODEL = "artifact"
    HREF_TEMPLATE = "artifacts/{pulp_id}/"
    ID_PREFIX = "artifacts"

    def upload(
        self,
        file: t.IO[bytes],
        chunk_size: int | None = None,
        sha256: str | None = None,
    ) -> t.Any:
        size = Path(file.name).stat().st_size

        sha256_hasher = hashlib.sha256()
        for chunk in iter(lambda: file.read(10_000_000), b""):
            sha256_hasher.update(chunk)
        sha256_digest = sha256_hasher.hexdigest()
        file.seek(0)

        if sha256 is not None and sha256_digest != sha256:
            raise PulpException(_("File digest does not match."))

        # check whether the file exists before uploading
        result = self.list(limit=1, offset=0, parameters={"sha256": sha256_digest})
        if len(result) > 0:
            self.pulp_ctx.echo(_("Artifact already exists."), err=True)
            self.pulp_href = result[0]["pulp_href"]
            return result[0]["pulp_href"]

        self.pulp_ctx.echo(_("Uploading file {filename}").format(filename=file.name), err=True)

        if self.pulp_ctx.fake_mode:
            self._entity = {"pulp_href": "<FAKE_ENTITY>", "sha256": sha256, "size": size}
            self._entity_lookup = {}
            return self._entity["pulp_href"]
        if chunk_size is None or chunk_size > size:
            # upload it directly
            artifact: dict[str, t.Any] = self.create({"sha256": sha256_digest, "file": file})
            self.pulp_href = artifact["pulp_href"]
            return artifact["pulp_href"]

        upload_ctx = PulpUploadContext(self.pulp_ctx)
        upload_ctx.upload_file(file, chunk_size)

        self.pulp_ctx.echo(_("Creating artifact."), err=True)
        try:
            task = upload_ctx.commit(sha256_digest)
        except Exception as e:
            upload_ctx.delete()
            raise e
        self.pulp_href = task["created_resources"][0]
        return task["created_resources"][0]


class PulpDomainContext(PulpEntityContext):
    ENTITY = _("Pulp domain")
    ENTITIES = _("Pulp domains")
    HREF = "domain_href"
    ID_PREFIX = "domains"


class PulpExporterContext(PulpEntityContext):
    ENTITY = _("Pulp exporter")
    ENTITIES = _("Pulp exporters")
    HREF = "pulp_exporter_href"
    ID_PREFIX = "exporters_core_pulp"


class PulpExportContext(PulpEntityContext):
    ENTITY = _("Pulp export")
    ENTITIES = _("Pulp exports")
    HREF = "pulp_pulp_export_href"
    ID_PREFIX = "exporters_core_pulp_exports"
    exporter: EntityDefinition

    @property
    def scope(self) -> dict[str, t.Any]:
        return {PulpExporterContext.HREF: self.exporter["pulp_href"]}


class PulpGroupContext(PulpEntityContext):
    ENTITY = _("user group")
    ENTITIES = _("user groups")
    HREF = "group_href"
    ID_PREFIX = "groups"
    CAPABILITIES = {"roles": []}

    def add_user(self, user: "PulpUserContext") -> None:
        pass

    def remove_user(self, user: "PulpUserContext") -> None:
        user_pk = user.pulp_href.split("/")[-2]
        group_user_ctx = PulpGroupUserContext(self.pulp_ctx, self)
        # This is a bad workaround, because the api is terrible.
        group_user_ctx._entity = {
            "pulp_href": f"{group_user_ctx.group_ctx.pulp_href}users/{user_pk}/"
        }
        group_user_ctx.delete()


class PulpGroupRoleContext(PulpEntityContext):
    ENTITY = _("group role")
    ENTITIES = _("group roles")
    HREF = "groups_group_role_href"
    ID_PREFIX = "groups_roles"
    NULLABLES = {"content_object"}
    group_ctx: PulpGroupContext

    def __init__(self, pulp_ctx: PulpContext, group_ctx: PulpGroupContext) -> None:
        super().__init__(pulp_ctx)
        self.group_ctx = group_ctx

    @property
    def scope(self) -> dict[str, t.Any]:
        return {self.group_ctx.HREF: self.group_ctx.pulp_href}


class PulpGroupUserContext(PulpEntityContext):
    ENTITY = _("group user")
    ENTITIES = _("group users")
    HREF = "groups_user_href"
    ID_PREFIX = "groups_users"
    group_ctx: PulpGroupContext

    def __init__(self, pulp_ctx: PulpContext, group_ctx: PulpGroupContext) -> None:
        super().__init__(pulp_ctx)
        self.group_ctx = group_ctx

    @property
    def scope(self) -> dict[str, t.Any]:
        return {self.group_ctx.HREF: self.group_ctx.pulp_href}


class PulpImporterContext(PulpEntityContext):
    ENTITY = _("Pulp importer")
    ENTITIES = _("Pulp importers")
    HREF = "pulp_importer_href"
    ID_PREFIX = "importers_core_pulp"


class PulpOrphanContext(PulpViewSetContext):
    ID_PREFIX = "orphans_cleanup"

    def cleanup(self, body: dict[str, t.Any] | None = None) -> t.Any:
        if body is not None:
            body = preprocess_payload(body)
        else:
            body = {}
        return self.call("cleanup", body=body)


class PulpCompositeContentGuardContext(PulpContentGuardContext):
    PLUGIN = "core"
    RESOURCE_TYPE = "composite"
    ENTITY = "composite content guard"
    ENTITIES = "composite content guards"
    HREF = "composite_content_guard_href"
    ID_PREFIX = "contentguards_core_composite"


class PulpContentRedirectContentGuardContext(PulpContentGuardContext):
    PLUGIN = "core"
    RESOURCE_TYPE = "content_redirect"
    ENTITY = "content redirect content guard"
    ENTITIES = "content redirect content guards"
    HREF = "content_redirect_content_guard_href"
    ID_PREFIX = "contentguards_core_content_redirect"


class PulpHeaderContentGuardContext(PulpContentGuardContext):
    PLUGIN = "core"
    RESOURCE_TYPE = "header"
    ENTITY = "header content guard"
    ENTITIES = "header content guards"
    HREF = "header_content_guard_href"
    ID_PREFIX = "contentguards_core_header"


class PulpRbacContentGuardContext(PulpContentGuardContext):
    PLUGIN = "core"
    RESOURCE_TYPE = "rbac"
    ENTITY = "RBAC content guard"
    ENTITIES = "RBAC content guards"
    HREF = "r_b_a_c_content_guard_href"
    ID_PREFIX = "contentguards_core_rbac"
    DOWNLOAD_ROLE: t.ClassVar[str] = "core.rbaccontentguard_downloader"
    CAPABILITIES = {"roles": []}

    def assign(
        self,
        href: str | None = None,
        users: list[str] | None = None,
        groups: list[str] | None = None,
    ) -> t.Any:
        body: EntityDefinition = {"users": users, "groups": groups}
        body["role"] = self.DOWNLOAD_ROLE
        return self.call("add_role", parameters={self.HREF: href or self.pulp_href}, body=body)

    def remove(
        self,
        href: str | None = None,
        users: list[str] | None = None,
        groups: list[str] | None = None,
    ) -> t.Any:
        body: EntityDefinition = {"users": users, "groups": groups}
        body["role"] = self.DOWNLOAD_ROLE
        return self.call("remove_role", parameters={self.HREF: href or self.pulp_href}, body=body)


class PulpRoleContext(PulpEntityContext):
    ENTITY = _("role")
    ENTITIES = _("roles")
    HREF = "role_href"
    ID_PREFIX = "roles"
    NULLABLES = {"description"}


class PulpSigningServiceContext(PulpEntityContext):
    ENTITY = _("signing service")
    ENTITIES = _("signing services")
    HREF = "signing_service_href"
    ID_PREFIX = "signing_services"
    HREF_PATTERN = r"signing-services/"


class PulpTaskContext(PulpEntityContext):
    ENTITY = _("task")
    ENTITIES = _("tasks")
    HREF = "task_href"
    ID_PREFIX = "tasks"
    CAPABILITIES = {"roles": []}
    PLUGIN = "core"
    MODEL = "task"
    HREF_TEMPLATE = "tasks/{pulp_id}/"

    resource_context: PulpEntityContext | None = None

    def cancel(self, task_href: str | None = None, background: bool = False) -> t.Any:
        task_href = task_href or self.pulp_href
        task = self.call(
            "cancel",
            parameters={self.HREF: task_href},
            body={"state": "canceled"},
        )
        if not background:
            self.pulp_ctx.echo(_("Waiting to cancel task {href}").format(href=task_href), err=True)
            task = self.pulp_ctx.wait_for_task(task, expect_cancel=True)
            self.pulp_ctx.echo(_("Done."), err=True)
        return task

    def profile_artifact_urls(self) -> dict[str, str]:
        self.pulp_ctx.needs_plugin(PluginRequirement("core", specifier=">=3.57.0"))
        result = self.call(
            "profile_artifacts",
            parameters={self.HREF: self.pulp_href},
        )["urls"]
        assert isinstance(result, dict)
        return result

    @property
    def scope(self) -> dict[str, t.Any]:
        if self.resource_context:
            return {"reserved_resources": self.resource_context.pulp_href}
        else:
            return {}

    def purge(
        self,
        finished_before: datetime.datetime | None,
        states: list[str] | None,
    ) -> t.Any:
        body: dict[str, t.Any] = {}
        if finished_before:
            body["finished_before"] = finished_before
        if states:
            body["states"] = states
        return self.call(
            "purge",
            body=body,
        )

    def summary(self) -> dict[str, int]:
        task_states = [
            "waiting",
            "skipped",
            "running",
            "completed",
            "failed",
            "canceling",
            "canceled",
        ]
        result = {}
        for state in task_states:
            payload = {"limit": 1, "state": state}
            result[state] = self.call("list", parameters=payload)["count"]
        return result


class PulpTaskGroupContext(PulpEntityContext):
    ENTITY = _("task group")
    ENTITIES = _("task groups")
    HREF = "task_group_href"
    ID_PREFIX = "task_groups"


class PulpUploadContext(PulpEntityContext):
    ENTITY = _("upload")
    ENTITIES = _("uploads")
    HREF = "upload_href"
    ID_PREFIX = "uploads"
    PLUGIN = "core"
    MODEL = "upload"
    HREF_TEMPLATE = "uploads/{pulp_id}/"

    def upload_chunk(
        self,
        chunk: bytes,
        size: int,
        start: int,
        non_blocking: bool = False,
    ) -> t.Any:
        end: int = start + len(chunk) - 1
        parameters = {self.HREF: self.pulp_href, "Content-Range": f"bytes {start}-{end}/{size}"}
        return self.call(
            "update",
            parameters=parameters,
            body={"sha256": hashlib.sha256(chunk).hexdigest(), "file": chunk},
            non_blocking=non_blocking,
        )

    def commit(self, sha256: str) -> t.Any:
        return self.call(
            "commit",
            parameters={self.HREF: self.pulp_href},
            body={"sha256": sha256},
        )

    def upload_file(self, file: t.IO[bytes], chunk_size: int = 1000000) -> t.Any:
        """Upload a file and return the uncommitted upload_href."""
        start = 0
        size = Path(file.name).stat().st_size
        upload_href = self.create(body={"size": size})["pulp_href"]
        try:
            self.pulp_href = upload_href
            while start < size:
                chunk = file.read(chunk_size)
                self.upload_chunk(
                    chunk=chunk,
                    size=size,
                    start=start,
                )
                start += chunk_size
                self.pulp_ctx.echo(".", nl=False, err=True)
        except Exception as e:
            self.delete(upload_href)
            raise e
        self.pulp_ctx.echo(_("Upload complete."), err=True)
        return upload_href


class PulpUserContext(PulpEntityContext):
    ENTITY = _("user")
    ENTITIES = _("users")
    HREF = "auth_user_href"
    ID_PREFIX = "users"
    NULLABLES = {"password"}


class PulpUserRoleContext(PulpEntityContext):
    ENTITY = _("user role")
    ENTITIES = _("user roles")
    HREF = "auth_users_user_role_href"
    ID_PREFIX = "users_roles"
    NULLABLES = {"content_object"}
    user_ctx: PulpUserContext

    def __init__(self, pulp_ctx: PulpContext, user_ctx: PulpUserContext) -> None:
        super().__init__(pulp_ctx)
        self.user_ctx = user_ctx

    @property
    def scope(self) -> dict[str, t.Any]:
        return {self.user_ctx.HREF: self.user_ctx.pulp_href}


class PulpWorkerContext(PulpEntityContext):
    ENTITY = _("worker")
    ENTITIES = _("workers")
    HREF = "worker_href"
    ID_PREFIX = "workers"
    HREF_PATTERN = r"workers/"


class PulpUpstreamPulpContext(PulpEntityContext):
    ENTITY = _("upstream pulp")
    ENTITIES = _("upstream pulps")
    HREF = "upstream_pulp_href"
    ID_PREFIX = "upstream_pulps"
    HREF_PATTERN = r"upstream-pulps/"

    def find(self, **kwargs: t.Any) -> t.Any:
        # Workaroud the missing ability to filter.
        # # TODO fix upstream and adjust to guard for the proper version
        # # https://github.com/pulp/pulpcore/issues/4110
        # if self.pulp_ctx.has_plugin(PluginRequirement("core", specifier=">=3.99.dev")):
        #     # Workaround not needed anymore
        #     return super().find(**kwargs)
        search_result = self.list(limit=sys.maxsize, offset=0, parameters={})
        for key, value in kwargs.items():
            search_result = [res for res in search_result if res[key] == value]
        if len(search_result) != 1:
            raise PulpException(
                _("Could not find {entity} with {kwargs}.").format(
                    entity=self.ENTITY, kwargs=kwargs
                )
            )
        return search_result[0]

    def replicate(self, body: EntityDefinition | None = None) -> t.Any:
        return self.call("replicate", parameters={self.HREF: self.pulp_href}, body=body or {})


class PulpVulnerabilityReportContext(PulpEntityContext):
    ENTITY = _("vulnerability report")
    ENTITIES = _("vulnerability reports")
    ID_PREFIX = "vuln_report"
    HREF = "vulnerability_report_href"
    NEEDS_PLUGINS = [PluginRequirement("core", specifier=">=3.85.3")]
