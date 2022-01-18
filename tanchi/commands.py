import typing

import tanjun

from tanchi import parser

__all__ = ["as_slash_command"]


def as_slash_command(
    name: str = None,
    *,
    always_defer: bool = False,
    default_permission: bool = True,
    default_to_ephemeral: typing.Optional[bool] = None,
    is_global: bool = True,
    sort_options: bool = True,
) -> typing.Callable[[typing.Callable[..., typing.Any]], tanjun.SlashCommand]:
    """Build a SlashCommand by decorating a function."""
    return lambda func: parser.create_command(
        func,
        name=name,
        always_defer=always_defer,
        default_permission=default_permission,
        default_to_ephemeral=default_to_ephemeral,
        is_global=is_global,
        sort_options=sort_options,
    )
