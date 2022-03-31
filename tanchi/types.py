from __future__ import annotations

import inspect
import sys
import typing

import hikari
import tanjun

__all__ = ["Range", "Converted", "Mentionable"]

T = typing.TypeVar("T")
MaybeAwaitable = typing.Union[typing.Awaitable[T], T]
CommandCallbackSigT = typing.TypeVar("CommandCallbackSigT", bound=tanjun.abc.CommandCallbackSig)

RangeValue = typing.Union[int, float]
RangeValueT = typing.TypeVar("RangeValueT", bound=RangeValue)

UNDEFINED_DEFAULT = tanjun.commands.slash.UNDEFINED_DEFAULT
"""Singleton for tanjun's undefined defaults."""


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


class RangeMeta(type):
    def __getitem__(
        self,
        args: typing.Tuple[typing.Union[RangeValueT, ellipsis], typing.Union[RangeValueT, ellipsis]],
    ) -> typing.Type[RangeValueT]:
        a, b = typing.cast("list[RangeValue]", [None if x is Ellipsis else x for x in args])
        r = Range(a, b)

        return typing.cast("type[RangeValueT]", r)


class Range(metaclass=RangeMeta):
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
            typing.Callable[..., MaybeAwaitable[T]],
            typing.Tuple[typing.Any, typing.Callable[..., MaybeAwaitable[T]]],
        ],
    ) -> typing.Type[T]:
        converter = args[-1] if isinstance(args, tuple) else args
        return typing.cast("type[T]", Converted(converter))


class Converted(metaclass=ConvertedMeta):
    converter: typing.Callable[..., MaybeAwaitable[typing.Any]]

    def __init__(self, converter: typing.Callable[..., MaybeAwaitable[typing.Any]]) -> None:
        self.converter = converter


Mentionable = typing.Union[hikari.Role, hikari.User]
"""Custom type denoting a Role or User."""
