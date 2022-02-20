"""Converters that are not availible in tanjun itself"""
import inspect
import typing

import hikari
import tanjun

__all__ = ["get_converters", "ToUnknownCustomEmoji", "ToUnicodeEmoji", "ToAnyEmoji"]

T = typing.TypeVar("T")


def get_converters(origin: typing.Optional[type] = None) -> typing.Mapping[typing.Any, typing.Any]:
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


class CachelessConverter(tanjun.conversion.BaseConverter[T]):
    @property
    def async_caches(self) -> typing.Sequence[typing.Any]:
        return ()

    @property
    def cache_components(self) -> hikari.CacheComponents:
        return hikari.CacheComponents.NONE

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
