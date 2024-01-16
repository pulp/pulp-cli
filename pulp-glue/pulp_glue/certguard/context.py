from pulp_glue.common.context import PluginRequirement, PulpContentGuardContext
from pulp_glue.common.i18n import get_translation

translation = get_translation(__package__)
_ = translation.gettext


class PulpX509CertGuardContext(PulpContentGuardContext):
    PLUGIN = "certguard"
    RESOURCE_TYPE = "x509"
    ENTITY = _("x509 certguard")
    ENTITIES = _("x509 certguards")
    HREF = "certguard_x509_cert_guard_href"
    ID_PREFIX = "contentguards_certguard_x509"
    NEEDS_PLUGINS = [PluginRequirement("certguard", specifier=">=1.4.0")]


class PulpRHSMCertGuardContext(PulpContentGuardContext):
    PLUGIN = "certguard"
    RESOURCE_TYPE = "rhsm"
    ENTITY = _("RHSM certguard")
    ENTITIES = _("RHSM certguards")
    HREF = "certguard_r_h_s_m_cert_guard_href"
    ID_PREFIX = "contentguards_certguard_rhsm"
    NEEDS_PLUGINS = [PluginRequirement("certguard", specifier=">=1.4.0")]
