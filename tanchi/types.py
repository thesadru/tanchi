from __future__ import annotations

import inspect
import sys
import typing

import hikari
import tanjun

__all__ = ["Range", "Converted", "Mentionable", "Autocompleted"]

T = typing.TypeVar("T")
MaybeAwaitable = typing.Union[typing.Coroutine[typing.Any, typing.Any, T], T]
MaybeSequence = typing.Union[typing.Sequence[T], T]
CommandCallbackSigT = typing.TypeVar("CommandCallbackSigT", bound=tanjun.abc.CommandCallbackSig)

RangeValue = typing.Union[int, float]
RangeValueT = typing.TypeVar("RangeValueT", bound=RangeValue)

UNDEFINED_DEFAULT = tanjun.commands.slash.UNDEFINED_DEFAULT
"""Singleton for tanjun's undefined defaults."""


Mentionable = typing.Union[hikari.Role, hikari.User]
"""Custom type denoting a Role or User."""


def signature(
    obj: typing.Callable[..., typing.Any],
    *,
    follow_wrapped: bool = True,
    eval_str: bool = True,
) -> inspect.Signature:
    if not eval_str:
        return inspect.signature(obj, follow_wrapped=True)

    if sys.version_info >= (3, 10):
        return inspect.signature(obj, follow_wrapped=follow_wrapped, eval_str=True)

    signature = inspect.signature(obj, follow_wrapped=True)
    resolved_typehints = typing.get_type_hints(obj, include_extras=True)

    params = []
    for name, param in signature.parameters.items():
        params.append(param.replace(annotation=resolved_typehints.get(name, inspect.Parameter.empty)))

    return_annotation = resolved_typehints.get("return", inspect.Parameter.empty)

    return signature.replace(parameters=params, return_annotation=return_annotation)


class SpecialType(type):
    def __new__(cls, *args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        return super().__new__(cls, cls.__name__, (), {})


class RangeMeta(type):
    # sometimes Range[1, 10] may be interpreted as Literal[1, 10] and we don't want that
    @typing.overload
    def __getitem__(  # type: ignore
        self,
        args: typing.Tuple[typing.Union[int, ellipsis], typing.Union[int, ellipsis]],
    ) -> typing.Type[int]:
        ...

    @typing.overload
    def __getitem__(
        self,
        args: typing.Tuple[typing.Union[float, ellipsis], typing.Union[float, ellipsis]],
    ) -> typing.Type[float]:
        ...

    def __getitem__(
        self,
        args: typing.Tuple[typing.Union[RangeValueT, ellipsis], typing.Union[RangeValueT, ellipsis]],
    ) -> typing.Type[RangeValueT]:
        a, b = typing.cast("list[RangeValue]", [None if x is Ellipsis else x for x in args])
        r = Range(a, b)

        return typing.cast("type[RangeValueT]", r)


class Range(SpecialType, metaclass=RangeMeta):
    min_value: typing.Optional[RangeValue]
    max_value: typing.Optional[RangeValue]
    underlying_type: typing.Optional[typing.Type[RangeValue]]

    def __init__(
        self,
        min_value: typing.Optional[RangeValue] = None,
        max_value: typing.Optional[RangeValue] = None,
    ) -> None:
        if min_value is None and max_value is None:
            raise TypeError("Either a min or max value is required")

        self.min_value = min_value
        self.max_value = max_value

        if isinstance(self.min_value, float) or isinstance(self.max_value, float):
            self.underlying_type = float
        else:
            self.underlying_type = int


class ConvertedMeta(type):
    def __getitem__(
        self,
        args: typing.Union[
            MaybeSequence[typing.Callable[..., MaybeAwaitable[T]]],
            typing.Tuple[typing.Type[T], MaybeSequence[typing.Callable[..., MaybeAwaitable[T]]]],
        ],
    ) -> typing.Type[T]:
        converters = args[1] if isinstance(args, tuple) and len(args) == 2 else args
        if not isinstance(converters, typing.Sequence):
            converters = (converters,)

        return typing.cast("type[T]", Converted(*converters))


class Converted(SpecialType, metaclass=ConvertedMeta):
    converters: typing.Sequence[tanjun.commands.slash.ConverterSig]

    def __init__(self, *converters: tanjun.commands.slash.ConverterSig) -> None:
        if len(converters) == 0:
            raise ValueError("At least one converter must be provided.")

        self.converters = converters


class AutocompletedMeta(type):
    @typing.overload
    def __getitem__(self, args: tanjun.abc.AutocompleteCallbackSig) -> typing.Type[str]:
        ...

    @typing.overload
    def __getitem__(
        self,
        args: typing.Tuple[tanjun.abc.AutocompleteCallbackSig, MaybeSequence[typing.Callable[..., MaybeAwaitable[T]]]],
    ) -> typing.Type[T]:
        ...

    def __getitem__(
        self,
        args: typing.Union[
            tanjun.abc.AutocompleteCallbackSig,
            typing.Tuple[tanjun.abc.AutocompleteCallbackSig, MaybeSequence[tanjun.commands.slash.ConverterSig]],
        ],
    ) -> typing.Type[typing.Any]:
        autocomplete, converters = args if isinstance(args, tuple) else (args, ())
        if not isinstance(converters, typing.Sequence):
            converters = (converters,)

        return typing.cast("type[typing.Any]", Autocompleted(autocomplete, *converters))


class Autocompleted(SpecialType, metaclass=AutocompletedMeta):
    autocomplete: tanjun.abc.AutocompleteCallbackSig
    converters: typing.Sequence[tanjun.commands.slash.ConverterSig]

    def __init__(
        self,
        autocomplete: tanjun.abc.AutocompleteCallbackSig,
        *converters: tanjun.commands.slash.ConverterSig,
    ) -> None:
        self.autocomplete = autocomplete  # type: ignore[assignment]
        self.converters = converters
