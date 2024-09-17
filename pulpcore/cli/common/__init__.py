import typing as t

import click

from pulpcore.cli.common.debug import debug

__version__ = "0.29.0"


def mount(main: click.Group, **kwargs: t.Any) -> None:
    main.add_command(debug)
