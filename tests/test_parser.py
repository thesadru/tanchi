import enum
import inspect
import typing
from unittest import mock

import hikari
import pytest
import tanjun

from tanchi import conversion, parser, types


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
    assert parser._try_channel_option(x) == [x]


def test_try_channel_option_with_union():
    x = typing.Union[hikari.GuildTextChannel, hikari.GuildVoiceChannel, None]
    assert parser._try_channel_option(x) == [
        hikari.GuildTextChannel,
        hikari.GuildVoiceChannel,
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
    command = mock.Mock(tanjun.SlashCommand)
    parser.parse_parameter(
        command,
        name="integer",
        description="description",
        annotation=int,
        default=inspect.Parameter.empty,
    )

    command._add_option.assert_called_once_with(
        "integer",
        "description",
        hikari.OptionType.INTEGER,
        default=types.UNDEFINED_DEFAULT,
        choices=None,
        min_value=None,
        max_value=None,
    )


def test_parse_parameter_with_string_choices():
    command = mock.Mock(tanjun.SlashCommand)
    parser.parse_parameter(
        command,
        name="string",
        description="description",
        annotation=typing.Literal["A", "B", "C"],
    )

    command._add_option.assert_called_once_with(
        "string",
        "description",
        hikari.OptionType.STRING,
        default=mock.ANY,
        choices={"A": "A", "B": "B", "C": "C"},
        min_value=mock.ANY,
        max_value=mock.ANY,
    )


def test_parse_parameter_with_user():
    command = mock.Mock(tanjun.SlashCommand)

    parser.parse_parameter(
        command,
        name="user",
        description="description",
        annotation=hikari.User,
    )
    command.add_user_option.assert_called_once_with(
        "user",
        "description",
        default=mock.ANY,
    )

    parser.parse_parameter(
        command,
        name="member",
        description="description",
        annotation=hikari.InteractionMember,
    )
    command.add_member_option.assert_called_once_with(
        "member",
        "description",
        default=mock.ANY,
    )


def test_parse_parameter_with_channel():
    command = mock.Mock(tanjun.SlashCommand)
    parser.parse_parameter(
        command,
        name="channel",
        description="description",
        annotation=typing.Union[hikari.GuildVoiceChannel, hikari.GuildStageChannel],
    )
    command.add_channel_option.assert_called_once_with(
        "channel",
        "description",
        default=mock.ANY,
        types=[hikari.GuildVoiceChannel, hikari.GuildStageChannel],
    )


def test_parse_parameter_with_range():
    command = mock.Mock(tanjun.SlashCommand)

    parser.parse_parameter(
        command,
        name="range",
        description="int range",
        annotation=types.Range(1, 2),
    )
    command._add_option.assert_called_once_with(
        "range",
        "int range",
        hikari.OptionType.INTEGER,
        default=mock.ANY,
        choices=None,
        min_value=1,
        max_value=2,
    )

    command = mock.Mock(tanjun.SlashCommand)
    parser.parse_parameter(
        command,
        name="range",
        description="float range",
        annotation=types.Range(0, 1.0),
    )
    command._add_option.assert_called_once_with(
        "range",
        "float range",
        hikari.OptionType.FLOAT,
        default=mock.ANY,
        choices=None,
        min_value=0,
        max_value=1.0,
    )


def test_parse_parameter_with_converter():
    command = mock.Mock(tanjun.SlashCommand)
    parser.parse_parameter(
        command,
        name="emoji",
        description="converter emoji",
        annotation=hikari.KnownCustomEmoji,
    )
    command.add_str_option.assert_called_once_with(
        "emoji",
        "converter emoji",
        default=mock.ANY,
        converters=[mock.ANY],
    )
    converter = command.add_str_option.call_args.kwargs["converters"][0]
    assert isinstance(converter, tanjun.conversion.ToEmoji)


def test_parse_parameter_with_misc():
    command = mock.Mock(tanjun.SlashCommand)

    with pytest.raises(TypeError):
        parser.parse_parameter(command, name="foo", annotation=object())
