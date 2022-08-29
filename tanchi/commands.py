import typing

import hikari
import tanjun

from tanchi import parser, types

__all__ = ["as_slash_command"]


def as_slash_command(
    name: typing.Optional[str] = None,
    *,
    always_defer: bool = False,
    default_member_permissions: typing.Union[hikari.Permissions, int, None] = None,
    default_to_ephemeral: typing.Optional[bool] = None,
    dm_enabled: typing.Optional[bool] = None,
    is_global: bool = True,
    sort_options: bool = True,
    validate_arg_keys: bool = True,
    **kwargs: typing.Any,
) -> typing.Callable[[types.CommandCallbackSigT], tanjun.SlashCommand[types.CommandCallbackSigT]]:
    """Build a SlashCommand by decorating a function."""
    return lambda func: parser.create_command(
        func,
        name=name,
        always_defer=always_defer,
        default_to_ephemeral=default_to_ephemeral,
        is_global=is_global,
        sort_options=sort_options,
        **kwargs,
    )
