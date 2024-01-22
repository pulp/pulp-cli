import gettext
import sys
from functools import lru_cache

if sys.version_info >= (3, 9):
    from importlib.resources import files
else:
    from importlib_resources import files


# Need to call lru_cache() before using it as a decorator for python 3.7 compatibility
@lru_cache(maxsize=None)
def get_translation(name: str) -> gettext.NullTranslations:
    """
    Return a translations object for a certain import path.

    Parameters:
        name: An import path.

    Returns:
        A `gettext` translations object containing all the `gettext` variations.

    Examples:
        Import the usual suspects like this:
        ```
        from pulp_glue.common.i18n import get_translation

        translation = get_translation(__package__)
        _ = translation.gettext
        ```
    """
    name_parts = name.split(".")
    while name_parts:
        try:
            localedir = files(".".join(name_parts)) / "locale"
            return gettext.translation("messages", localedir=str(localedir), fallback=True)
        except TypeError:
            name_parts.pop()
    raise TypeError(f"No package found for {name}.")
