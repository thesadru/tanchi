"""Converters that are not availible in tanjun itself"""
import abc
import datetime
import inspect
import re
import typing

import hikari
import tanjun

__all__ = ["get_converters", "ToUnknownCustomEmoji", "ToUnicodeEmoji", "ToAnyEmoji"]

T = typing.TypeVar("T")


def get_converters(
    origin: typing.Optional[type] = None,
) -> typing.Mapping[typing.Any, tanjun.commands.slash.ConverterSig]:
    """Get all created converters recursively"""
    origin = origin or tanjun.conversion.BaseConverter

    converters: typing.Dict[typing.Any, typing.Any] = {}

    for subclass in origin.__subclasses__():
        if not (bases := getattr(subclass, "__orig_bases__")):
            continue

        result_type = typing.get_args(bases[0])[0]

        if isinstance(result_type, typing.TypeVar):
            converters |= get_converters(subclass)
        elif not inspect.isabstract(subclass):
            instance = subclass()  # type: ignore[abstract]
            converters[result_type] = instance

    return converters


class CachelessConverter(tanjun.conversion.BaseConverter[T], abc.ABC):
    @property
    def async_caches(self) -> typing.Sequence[typing.Any]:
        return ()

    @property
    def cache_components(self) -> hikari.api.CacheComponents:
        return hikari.api.CacheComponents.NONE

    @property
    def intents(self) -> hikari.Intents:
        return hikari.Intents.NONE

    @property
    def requires_cache(self) -> bool:
        return False


class ToUnknownCustomEmoji(CachelessConverter[hikari.CustomEmoji]):
    __call__ = hikari.CustomEmoji.parse


class ToUnicodeEmoji(CachelessConverter[hikari.UnicodeEmoji]):
    __call__ = hikari.UnicodeEmoji.parse


class ToAnyEmoji(CachelessConverter[hikari.Emoji]):
    __call__ = hikari.Emoji.parse


class ToColor(CachelessConverter[hikari.Color]):
    __call__ = hikari.Color.of


class ToSnowflake(CachelessConverter[hikari.Snowflake]):
    __call__ = hikari.Snowflake


class ToDatetime(CachelessConverter[datetime.datetime]):
    def __call__(self, argument: str) -> datetime.datetime:
        if match := re.search(r"<t:(\d+)(?::[tTdDfFR])?>", argument):
            argument = match[1]

        try:
            return datetime.datetime.fromtimestamp(float(argument), tz=datetime.timezone.utc)
        except (ValueError, TypeError, OverflowError):
            pass

        try:
            return datetime.datetime.fromisoformat(argument).astimezone(datetime.timezone.utc)
        except ValueError:
            pass

        raise ValueError("Could not parse the date")
