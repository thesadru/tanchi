import enum
import functools
import typing
from unittest import mock

import hikari
import pytest
import tanjun

from tanchi import conversion, parser, types


def parse_parameter(annotation: typing.Any, *, name: str = "option") -> parser.Option:
    option = parser.parse_parameter(name=name, annotation=annotation)
    assert option is not None

    return option


def test_strip_optional():
    x = typing.Optional[int]
    assert parser._strip_optional(x) is int


def test_strip_optional_with_union():
    x = typing.Optional[typing.Union[int, str]]
    assert parser._strip_optional(x) == typing.Union[str, int]


def test_strip_optional_with_misc():
    x = object()
    assert parser._strip_optional(x) is x


def test_try_enum_option_with_enum():
    class Color(enum.IntEnum):
        red = 0xFF0000
        green = 0x00FF00
        blue = 0x0000FF

    assert parser._try_enum_option(Color) == {
        "red": 0xFF0000,
        "green": 0x00FF00,
        "blue": 0x0000FF,
    }


def test_try_enum_option_with_literal():
    x = typing.Literal[1, 2, 3]
    assert parser._try_enum_option(x) == {"1": 1, "2": 2, "3": 3}


def test_try_enum_option_with_misc():
    x = object()
    assert parser._try_enum_option(x) is None


def test_try_channel_option_with_single():
    x = hikari.GuildTextChannel
    assert parser._try_channel_option(x) == [hikari.ChannelType.GUILD_TEXT]


def test_try_channel_option_with_union():
    x = typing.Union[hikari.GuildTextChannel, hikari.GuildVoiceChannel, None]
    assert parser._try_channel_option(x) == [
        hikari.ChannelType.GUILD_TEXT,
        hikari.ChannelType.GUILD_VOICE,
    ]


def test_try_channel_option_with_misc():
    x = typing.Optional[object]
    assert parser._try_channel_option(x) is None


def test_try_convertered_option_with_single():
    x = hikari.UnicodeEmoji
    converters = parser._try_convertered_option(x)

    assert converters
    assert isinstance(converters[0], conversion.ToUnicodeEmoji)


def test_try_convertered_option_with_union():
    x = typing.Union[hikari.Invite, hikari.InviteWithMetadata]
    converters = parser._try_convertered_option(x)

    assert converters
    assert isinstance(converters[0], tanjun.conversion.ToInvite)
    assert isinstance(converters[1], tanjun.conversion.ToInviteWithMetadata)


def test_parse_parameter_with_int():
    option = parse_parameter(int)

    assert option.option_type == hikari.OptionType.INTEGER
    assert option.min_value is None and option.max_value is None


def test_parse_parameter_with_string_choices():
    option = parse_parameter(typing.Literal["A", "B", "C"])

    assert option.option_type == hikari.OptionType.STRING
    assert option.choices == {v: v for v in ("A", "B", "C")}


def test_parse_parameter_with_user():
    option = parse_parameter(hikari.User)

    assert option.option_type == hikari.OptionType.USER
    assert not option.only_member

    option = parse_parameter(hikari.InteractionMember)

    assert option.option_type == hikari.OptionType.USER
    assert option.only_member


def test_parse_parameter_with_channel():
    option = parse_parameter(typing.Union[hikari.GuildVoiceChannel, hikari.GuildStageChannel])

    assert option.option_type == hikari.OptionType.CHANNEL
    assert option.channel_types == [hikari.ChannelType.GUILD_VOICE, hikari.ChannelType.GUILD_STAGE]


def test_parse_parameter_with_range():
    option = parse_parameter(types.Range(1, 2))

    assert option.option_type == hikari.OptionType.INTEGER
    assert option.min_value == 1 and option.max_value == 2

    option = parse_parameter(types.Range[0.0, ...])

    assert option.option_type == hikari.OptionType.FLOAT
    assert option.min_value == 0 and option.max_value is None


def test_parse_parameter_with_converter():
    option = parse_parameter(hikari.KnownCustomEmoji, name="emoji")
    assert option.option_type == hikari.OptionType.STRING
    assert option.converters[0].__class__ is tanjun.conversion.ToEmoji


def test_parse_parameter_with_converter_class():
    option = parse_parameter(types.Converted[int], name="bigint")

    assert option.option_type == hikari.OptionType.STRING
    assert option.converters == (int,)

    option = parse_parameter(types.Converted[int, round], name="bigint")

    assert option.option_type == hikari.OptionType.STRING
    assert option.converters == (round,)


def test_parse_parameter_with_annotated_class():
    autocomplete = mock.Mock()

    option = parse_parameter(types.Autocompleted[autocomplete])
    assert option.option_type == hikari.OptionType.STRING
    assert option.autocomplete and option.autocomplete.__wrapped__ == autocomplete
    assert not option.converters

    option = parse_parameter(types.Autocompleted[autocomplete, int])
    assert option.option_type == hikari.OptionType.STRING
    assert option.autocomplete and option.autocomplete.__wrapped__ == autocomplete
    assert not option.converters == [int]


def test_parse_parameter_with_misc():

    with pytest.raises(TypeError):
        option = parse_parameter(annotation=object())
