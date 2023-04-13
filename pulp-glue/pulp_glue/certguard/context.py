from pulp_glue.common.context import PluginRequirement
from pulp_glue.common.i18n import get_translation
from pulp_glue.core.context import PulpContentGuardContext

translation = get_translation(__name__)
_ = translation.gettext


class PulpX509CertGuardContext(PulpContentGuardContext):
    ENTITY = _("x509 certguard")
    ENTITIES = _("x509 certguards")
    HREF = "certguard_x509_cert_guard_href"
    ID_PREFIX = "contentguards_certguard_x509"
    NEEDS_PLUGINS = [PluginRequirement("certguard", min="1.4.0")]


class PulpRHSMCertGuardContext(PulpContentGuardContext):
    ENTITY = _("RHSM certguard")
    ENTITIES = _("RHSM certguards")
    HREF = "certguard_r_h_s_m_cert_guard_href"
    ID_PREFIX = "contentguards_certguard_rhsm"
    NEEDS_PLUGINS = [PluginRequirement("certguard", min="1.4.0")]
