from typing import IO, Any, ClassVar, Optional

import click

from pulpcore.cli.common.context import (
    EntityDefinition,
    PluginRequirement,
    PulpContentContext,
    PulpEntityContext,
    PulpRemoteContext,
    PulpRepositoryContext,
    PulpRepositoryVersionContext,
    registered_repository_contexts,
)
from pulpcore.cli.common.i18n import get_translation

translation = get_translation(__name__)
_ = translation.gettext


class PulpRpmACSContext(PulpEntityContext):
    ENTITY = _("rpm ACS")
    ENTITIES = _("rpm ACSes")
    HREF = "rpm_rpm_alternate_content_source_href"
    ID_PREFIX = "acs_rpm_rpm"

    def refresh(self, href: str) -> Any:
        return self.call(
            "refresh",
            parameters={self.HREF: href},
        )


class PulpRpmCompsXmlContext(PulpEntityContext):
    UPLOAD_COMPS_ID: ClassVar[str] = "rpm_comps_upload"

    def upload_comps(
        self, file: IO[bytes], repo_href: Optional[str], replace: Optional[bool]
    ) -> Any:
        click.echo(_("Uploading file {filename}").format(filename=file.name), err=True)
        file.seek(0)
        return self.call(
            "upload_comps",
            uploads={"file": file.read()},
            body={"repository": repo_href, "replace": replace},
        )


class PulpRpmDistributionContext(PulpEntityContext):
    ENTITY = _("rpm distribution")
    ENTITIES = _("rpm distributions")
    HREF = "rpm_rpm_distribution_href"
    ID_PREFIX = "distributions_rpm_rpm"
    NULLABLES = {"publication", "repository"}

    def preprocess_body(self, body: EntityDefinition) -> EntityDefinition:
        body = super().preprocess_body(body)
        if self.pulp_ctx.has_plugin(PluginRequirement("core", min="3.16.0.dev")):
            if "repository" in body and "publication" not in body:
                body["publication"] = None
            if "repository" not in body and "publication" in body:
                body["repository"] = None
        return body


class PulpRpmPackageContext(PulpContentContext):
    ENTITY = "rpm package"
    ENTITIES = "rpm packages"
    HREF = "rpm_package_href"
    ID_PREFIX = "content_rpm_packages"


class PulpRpmPublicationContext(PulpEntityContext):
    ENTITY = _("rpm publication")
    ENTITIES = _("rpm publications")
    HREF = "rpm_rpm_publication_href"
    ID_PREFIX = "publications_rpm_rpm"

    def preprocess_body(self, body: EntityDefinition) -> EntityDefinition:
        body = super().preprocess_body(body)
        version = body.pop("version", None)
        if version is not None:
            repository_href = body.pop("repository")
            body["repository_version"] = f"{repository_href}versions/{version}/"
        return body


class PulpRpmRemoteContext(PulpRemoteContext):
    ENTITY = _("rpm remote")
    ENTITIES = _("rpm remotes")
    HREF = "rpm_rpm_remote_href"
    ID_PREFIX = "remotes_rpm_rpm"
    NULLABLES = {
        "ca_cert",
        "client_cert",
        "client_key",
        "username",
        "password",
        "proxy_url",
        "proxy_username",
        "proxy_password",
        "sles_auth_token",
    }


class PulpRpmRepositoryVersionContext(PulpRepositoryVersionContext):
    HREF = "rpm_rpm_repository_version_href"
    ID_PREFIX = "repositories_rpm_rpm_versions"


class PulpRpmRepositoryContext(PulpRepositoryContext):
    HREF = "rpm_rpm_repository_href"
    ID_PREFIX = "repositories_rpm_rpm"
    VERSION_CONTEXT = PulpRpmRepositoryVersionContext
    CAPABILITIES = {"pulpexport": [PluginRequirement("rpm")]}


registered_repository_contexts["rpm:rpm"] = PulpRpmRepositoryContext
