import functools
import inspect
import typing

import hikari
import tanjun

from tanchi import types

__all__ = ["as_autocomplete", "with_autocomplete"]

AutocompleteSig = typing.Callable[..., types.MaybeAwaitable[typing.Optional[types.Choices]]]


def as_autocomplete(callback: AutocompleteSig) -> tanjun.abc.AutocompleteCallbackSig:
    """Convert a callback to an autocomplete callback."""

    @functools.wraps(callback)
    async def wrapper(context: tanjun.abc.AutocompleteContext, *args: typing.Any, **kwargs: typing.Any) -> None:
        result = callback(context, *args, **kwargs)
        if inspect.isawaitable(result):
            result = await result

        result = typing.cast("typing.Optional[types.Choices]", result)

        if result is None or context.has_responded:
            return

        if isinstance(result, typing.Sequence):
            result = {str(value): value for value in result}

        await context.set_choices(result)  # type: ignore # choices have to have the same type

    return wrapper


def with_autocomplete(
    command: tanjun.SlashCommand[typing.Any],
    /,
    name: str,
) -> typing.Callable[[AutocompleteSig], tanjun.abc.AutocompleteCallbackSig]:
    """Decorator to add an arbitrary autocomplete to a command."""
    option = command._builder.get_option(name)
    if not option:
        raise KeyError("Option not found")

    tp = option.type

    def wrapper(callback: AutocompleteSig) -> tanjun.abc.AutocompleteCallbackSig:
        autocompleter = as_autocomplete(callback)

        if tp == hikari.OptionType.STRING:
            command.set_str_autocomplete(name, autocompleter)
        elif tp == hikari.OptionType.INTEGER:
            command.set_int_autocomplete(name, autocompleter)
        elif tp == hikari.OptionType.FLOAT:
            command.set_float_autocomplete(name, autocompleter)
        else:
            raise ValueError("Unsupported option type")

        return autocompleter

    return wrapper
