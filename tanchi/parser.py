from __future__ import annotations

import enum
import inspect
import re
import sys
import types
import typing

import hikari
import tanjun

from .types import UNDEFINED_DEFAULT, Mentionable, Range, signature

if typing.TYPE_CHECKING:
    from typing_extensions import TypeGuard

    T = typing.TypeVar("T")
    S = typing.TypeVar("S", bound=typing.Type[typing.Any])


__all__ = ["parse_parameter", "parse_docstring", "create_command"]


if sys.version_info >= (3, 10):
    _UnionTypes = {typing.Union, types.UnionType}
    _NoneTypes = {None, types.NoneType}

else:
    _UnionTypes = {typing.Union}
    _NoneTypes = {None, type(None)}

_AnnotatedAlias = type(typing.Annotated[object, object])

_builtin_type_mapping: typing.Mapping[type, hikari.OptionType] = {
    str: hikari.OptionType.STRING,
    int: hikari.OptionType.INTEGER,
    float: hikari.OptionType.FLOAT,
    bool: hikari.OptionType.BOOLEAN,
}
"""Generic discord types with builtin equivalents"""

_hikari_type_mapping: typing.Mapping[typing.Any, int] = {
    hikari.Role: hikari.OptionType.ROLE,
    Mentionable: hikari.OptionType.MENTIONABLE,
    hikari.Attachment: 11,
}
"""Generic discord types with hikari equivalents"""


def issubclass_(obj: typing.Any, tp: S) -> TypeGuard[S]:
    """More lenient issubclass"""
    return isinstance(obj, type) and issubclass(obj, tp)


def _strip_optional(tp: typing.Any) -> typing.Any:
    """Remove all None from a union"""
    if typing.get_origin(tp) not in _UnionTypes:
        return tp

    args = [x for x in typing.get_args(tp) if x not in _NoneTypes]
    if len(args) == 1:
        return args[0]

    # pyright doesn't understand this so we have to ignore
    return typing.Union[tuple(args)]  # type: ignore


def _try_enum_option(
    tp: typing.Any,
) -> typing.Optional[typing.Mapping[str, typing.Any]]:
    """Try parsing a literal or an enum into a list of arguments"""
    if typing.get_origin(tp) == typing.Literal:
        return {str(x): x for x in typing.get_args(tp)}

    # Users may attempt to use their own enums
    if members := getattr(tp, "__members__", None):
        return {name: value for name, value in members.items()}

    return None


def _try_channel_option(
    tp: typing.Any,
) -> typing.Optional[typing.Sequence[typing.Type[hikari.PartialChannel]]]:
    """Try parsing an annotation into channel types"""
    if typing.get_origin(tp) in _UnionTypes:
        args = [x for x in typing.get_args(tp) if x not in _NoneTypes]
    else:
        args = [tp]

    for arg in args:
        if not issubclass_(arg, hikari.PartialChannel):
            return None

    return args


def parse_parameter(
    command: tanjun.SlashCommand[typing.Any],
    name: str,
    annotation: typing.Any,
    default: typing.Any = UNDEFINED_DEFAULT,
    description: typing.Optional[str] = None,
) -> None:
    """Parse a parameter in a command signature."""
    if isinstance(annotation, _AnnotatedAlias):
        # should we really only care about the first one?
        annotation = typing.get_args(annotation)[1]

    annotation = _strip_optional(annotation)
    description = description or "-"

    if default is inspect.Parameter.empty:
        default = UNDEFINED_DEFAULT

    choices = None
    if choices := _try_enum_option(annotation):
        # surely the user wouldn't mix types right?
        annotation = type(next(iter(choices.values())))

    min_value, max_value = None, None
    if isinstance(annotation, Range):
        min_value, max_value = annotation.min_value, annotation.max_value
        annotation = annotation.underlying_type

    if option_type := _builtin_type_mapping.get(annotation):
        command._add_option(
            name,
            description,
            option_type,
            default=default,
            choices=choices,
            min_value=min_value,
            max_value=max_value,
        )
        return

    for tp, option_tp in _hikari_type_mapping.items():
        if issubclass_(annotation, tp):
            command._add_option(
                name,
                description,
                option_tp,
                default=default,
            )
            return

    if issubclass_(annotation, hikari.Member):
        command.add_member_option(name, description, default=default)
    elif issubclass_(annotation, hikari.PartialUser):
        command.add_user_option(name, description, default=default)

    elif types := _try_channel_option(annotation):
        command.add_channel_option(name, description, default=default, types=types)

    else:
        raise TypeError(f"Unknown slash command option type: {annotation!r}")


def parse_docstring(docstring: str) -> typing.Tuple[str, typing.Mapping[str, str]]:
    """Parse a docstring and get all parameter descriptions"""
    # TODO: Allow more than sphinx

    docstring = inspect.cleandoc(docstring)

    main = docstring.splitlines()[0]
    parameters = {}

    if match := re.search(r"Parameters\s*\n\s*-+\s*((?:.|\n)*)(\n{2,})?", docstring):
        # ReST
        docstring = match[1]
        for match in re.finditer(r"(\w+)\s*:.*\n\s+(.+)", docstring):
            name, desc = match[1], match[2]
            parameters[name] = " ".join(x.strip() for x in desc.splitlines())
    elif match := re.search(r"Args\s*:\s*\n((?:.|\n)*)(\n{2,})?", docstring):
        # Google
        docstring = match[1]
        for match in re.finditer(r"\s*(\w+)\s*(?:\(.+?\))?:\s+(.+)", docstring):
            name, desc = match[1], match[2]
            parameters[name] = " ".join(x.strip() for x in desc.splitlines())

    return main, parameters


def create_command(
    function: tanjun.abc.CommandCallbackSigT,
    *,
    name: typing.Optional[str] = None,
    always_defer: bool = False,
    default_permission: bool = True,
    default_to_ephemeral: typing.Optional[bool] = None,
    is_global: bool = True,
    sort_options: bool = True,
) -> tanjun.SlashCommand[tanjun.abc.CommandCallbackSigT]:
    """Build a SlashCommand."""
    if not (doc := function.__doc__):
        raise TypeError("Function missing docstring, cannot create descriptions")

    description, parameter_descriptions = parse_docstring(doc)

    command = tanjun.SlashCommand(
        function,
        name or function.__name__,
        description,
        always_defer=always_defer,
        default_permission=default_permission,
        default_to_ephemeral=default_to_ephemeral,
        is_global=is_global,
        sort_options=sort_options,
    )

    sig = signature(function)
    parameters = iter(sig.parameters.values())
    context_paramter = next(parameters)

    for parameter in parameters:
        if isinstance(parameter.default, tanjun.injecting.Injected):
            # keep in the signature
            continue

        parse_parameter(
            command,
            name=parameter.name,
            description=parameter_descriptions.get(parameter.name, "-"),
            annotation=parameter.annotation,
            default=parameter.default,
        )

    return command
