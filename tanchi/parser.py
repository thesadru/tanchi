from __future__ import annotations

import inspect
import re
import sys
import typing

import alluka
import hikari
import tanjun

from . import conversion, types

if typing.TYPE_CHECKING:
    from typing_extensions import TypeGuard

    T = typing.TypeVar("T")
    TryReturnT = typing.TypeVar("TryReturnT", bound=typing.Optional[typing.Sequence[typing.Any]])
    S = typing.TypeVar("S", bound=typing.Type[typing.Any])


__all__ = ["create_command", "parse_docstring", "parse_parameter"]


if sys.version_info >= (3, 10):
    from types import NoneType, UnionType

    _UnionTypes = {typing.Union, UnionType}
    _NoneTypes = {None, NoneType}

else:
    _UnionTypes = {typing.Union}
    _NoneTypes = {None, type(None)}

_UndefinedTypes = {hikari.UNDEFINED, hikari.UndefinedType, typing.Literal[hikari.UNDEFINED]}
_AnnotatedAlias = type(typing.Annotated[object, object])

_builtin_type_mapping: typing.Mapping[type, hikari.OptionType] = {
    str: hikari.OptionType.STRING,
    int: hikari.OptionType.INTEGER,
    float: hikari.OptionType.FLOAT,
    bool: hikari.OptionType.BOOLEAN,
}
"""Generic discord types with builtin equivalents"""

_hikari_type_mapping: typing.Mapping[typing.Any, hikari.OptionType] = {
    hikari.Role: hikari.OptionType.ROLE,
    types.Mentionable: hikari.OptionType.MENTIONABLE,
    hikari.Attachment: hikari.OptionType.ATTACHMENT,
}
"""Generic discord types with hikari equivalents"""


def issubclass_(obj: typing.Any, tp: S) -> TypeGuard[S]:
    """More lenient issubclass"""
    if isinstance(tp, typing._GenericAlias):  # type: ignore
        return obj == tp

    return isinstance(obj, type) and issubclass(obj, tp)


def _get_value_args(tp: typing.Any, exclude: typing.Collection[typing.Any] = _NoneTypes) -> typing.Sequence[typing.Any]:
    """Get all args that are not None"""
    return [x for x in typing.get_args(tp) if x not in exclude]


def support_union(func: typing.Callable[[typing.Any], TryReturnT]) -> typing.Callable[[typing.Any], TryReturnT]:
    """Make a function support returning sequences if a union is passed in"""

    def wrapper(tp: typing.Any) -> typing.Any:
        if typing.get_origin(tp) not in _UnionTypes:
            return func(tp)

        results: typing.List[typing.Any] = []

        for x in _get_value_args(tp):
            value: typing.Sequence[typing.Any] = wrapper(x)
            if not value:
                return None

            results += value

        return results

    return wrapper


def _strip_optional(tp: typing.Any, exclude: typing.Collection[typing.Any] = _NoneTypes) -> typing.Any:
    """Remove all None from a union"""
    if typing.get_origin(tp) not in _UnionTypes:
        return tp

    args = _get_value_args(tp, exclude=exclude)
    if len(args) == 1:
        return args[0]

    # pyright doesn't understand this so we have to ignore
    return typing.Union[tuple(args)]  # type: ignore


def _try_enum_option(tp: typing.Any) -> typing.Optional[typing.Mapping[str, typing.Any]]:
    """Try parsing a literal or an enum into a list of arguments"""
    if typing.get_origin(tp) == typing.Literal:
        # str.capitalize mimics the behavior of tanjun
        return {str(x).capitalize(): x for x in typing.get_args(tp)}

    # Users may attempt to use their own enums
    if members := getattr(tp, "__members__", None):
        return {name: getattr(value, "value", value) for name, value in members.items()}

    return None


@support_union
def _try_channel_option(tp: typing.Any) -> typing.Optional[typing.Sequence[typing.Type[hikari.PartialChannel]]]:
    """Try parsing an annotation into channel types"""
    if issubclass_(tp, hikari.PartialChannel):
        return [tp]

    return None


@support_union
def _try_convertered_option(tp: typing.Any) -> typing.Optional[typing.Sequence[tanjun.commands.slash.ConverterSig]]:
    """Try parsing an annotation into all the converters it would need"""
    if tp == str:
        # valid converter if used as a fallback
        return [str]

    if isinstance(tp, types.Converted):
        return tp.converters

    converters = conversion.get_converters()
    if converter := converters.get(tp):
        return [converter]

    return None


def parse_parameter(
    command: tanjun.SlashCommand[typing.Any],
    name: str,
    annotation: typing.Any,
    default: typing.Any = types.UNDEFINED_DEFAULT,
    description: typing.Optional[str] = None,
) -> None:
    """Parse a parameter in a command signature."""
    if isinstance(annotation, _AnnotatedAlias):
        # should we really only care about the first one?
        annotation = typing.get_args(annotation)[1]

    if isinstance(annotation, alluka._types.InjectedTypes):
        return

    annotation = _strip_optional(annotation, exclude=_NoneTypes | _UndefinedTypes | {typing.Literal[default]})  # type: ignore
    description = description or "-"

    if default is inspect.Parameter.empty:
        default = types.UNDEFINED_DEFAULT

    if annotation is inspect.Parameter.empty:
        raise TypeError(f"Missing annotation for slash command option {name!r}")

    choices = None
    if choices := _try_enum_option(annotation):
        # surely the user wouldn't mix types right?
        annotation = type(next(iter(choices.values())))

    min_value, max_value = None, None
    if isinstance(annotation, types.Range):
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
        return
    elif issubclass_(annotation, hikari.PartialUser):
        command.add_user_option(name, description, default=default)
        return

    if channel_types := _try_channel_option(annotation):
        command.add_channel_option(name, description, default=default, types=channel_types)
        return

    if converters := _try_convertered_option(annotation):
        command.add_str_option(name, description, default=default, converters=converters)
        return

    if isinstance(annotation, types.Autocompleted):
        command.add_str_option(
            name,
            description,
            autocomplete=annotation.autocomplete,
            converters=annotation.converters,
        )
        return

    raise TypeError(f"Unknown slash command option type: {annotation!r}")


def parse_docstring(docstring: str) -> typing.Tuple[str, typing.Mapping[str, str]]:
    """Parse a docstring and get all parameter descriptions"""
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
    function: types.CommandCallbackSigT,
    *,
    name: typing.Optional[str] = None,
    always_defer: bool = False,
    default_member_permissions: typing.Union[hikari.Permissions, int, None] = None,
    default_to_ephemeral: typing.Optional[bool] = None,
    dm_enabled: typing.Optional[bool] = None,
    is_global: bool = True,
    sort_options: bool = True,
    validate_arg_keys: bool = True,
    **kwargs: typing.Any,
) -> tanjun.SlashCommand[types.CommandCallbackSigT]:
    """Build a SlashCommand."""
    if not (doc := function.__doc__):
        raise TypeError("Function missing docstring, cannot create descriptions")

    description, parameter_descriptions = parse_docstring(doc)

    command = tanjun.SlashCommand(
        function,
        name or function.__name__,
        description,
        always_defer=always_defer,
        default_member_permissions=default_member_permissions,
        default_to_ephemeral=default_to_ephemeral,
        dm_enabled=dm_enabled,
        is_global=is_global,
        sort_options=sort_options,
        validate_arg_keys=validate_arg_keys,
        **kwargs,
    )

    sig = types.signature(function)
    parameters = iter(sig.parameters.values())
    context_parameter = next(parameters)

    if context_parameter.annotation is not inspect.Parameter.empty:
        if not issubclass_(context_parameter.annotation, tanjun.abc.Context):
            raise TypeError("First argument in a slash command must be the context.")

    for parameter in parameters:
        if isinstance(parameter.default, alluka._types.InjectedDescriptor):
            continue

        parse_parameter(
            command,
            name=parameter.name,
            description=parameter_descriptions.get(parameter.name, "-"),
            annotation=parameter.annotation,
            default=parameter.default,
        )

    return command
