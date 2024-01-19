import typing as t

import click
from pulp_glue.common.i18n import get_translation
from pulpcore.cli.common.generic import pulp_group

# TODO Implement these
# from pulpcore.cli.{{ cookiecutter.app_label }}.content import content
# from pulpcore.cli.{{ cookiecutter.app_label }}.distribution import distribution
# from pulpcore.cli.{{ cookiecutter.app_label }}.publication import publication
# from pulpcore.cli.{{ cookiecutter.app_label }}.remote import remote
# from pulpcore.cli.{{ cookiecutter.app_label }}.repository import repository

translation = get_translation(__package__)
_ = translation.gettext

__version__ = "{{ cookiecutter.version }}"


@pulp_group(name="{{ cookiecutter.app_label }}")
def {{ cookiecutter.app_label }}_group() -> None:
    pass


def mount(main: click.Group, **kwargs: t.Any) -> None:
    # {{ cookiecutter.app_label }}_group.add_command(content)
    # {{ cookiecutter.app_label }}_group.add_command(distribution)
    # {{ cookiecutter.app_label }}_group.add_command(publication)
    # {{ cookiecutter.app_label }}_group.add_command(remote)
    # {{ cookiecutter.app_label }}_group.add_command(repository)
    main.add_command({{ cookiecutter.app_label }}_group)
