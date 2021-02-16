import gettext
from functools import lru_cache

import pkg_resources


def get_translation(name: str) -> gettext.NullTranslations:
    localedir = pkg_resources.resource_filename(name, "locale")
    return _get_translation_for_domain("messages", localedir)


# Need to call lru_cache() before using it as a decorator for python 3.7 compatibility
@lru_cache(maxsize=None)
def _get_translation_for_domain(domain: str, localedir: str) -> gettext.NullTranslations:
    return gettext.translation(domain, localedir=localedir, fallback=True)
