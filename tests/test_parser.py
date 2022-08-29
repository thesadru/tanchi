import enum
import functools
import typing
from unittest import mock

import hikari
import pytest
import tanjun

from tanchi import conversion, parser, types


class SlashCommand(tanjun.SlashCommand[typing.Any]):
    def __init__(self) -> None:
        super().__init__(lambda ctx, **kwargs: None, "name", "description")


def parse_parameter(
    command: tanjun.SlashCommand[typing.Any],
    annotation: typing.Any,
    *,
    name: str = "option",
    default: typing.Any = types.UNDEFINED_DEFAULT,
) -> None:
    parser.parse_parameter(
        command,
        name=name,
        annotation=annotation,
        default=default,
    )


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
    command = SlashCommand()

    parse_parameter(command, int)

    option = command._builder.options[0]
    assert option.type == hikari.OptionType.INTEGER
    assert option.min_value is None and option.max_value is None


def test_parse_parameter_with_string_choices():
    command = SlashCommand()

    parse_parameter(command, typing.Literal["A", "B", "C"])

    option = command._builder.options[0]
    assert option.type == hikari.OptionType.STRING
    assert option.choices == [hikari.CommandChoice(name=value, value=value) for value in ("A", "B", "C")]


def test_parse_parameter_with_user():
    command = SlashCommand()

    parse_parameter(command, hikari.User, name="user")
    parse_parameter(command, hikari.InteractionMember, name="member")

    assert command._builder.options[0].type == hikari.OptionType.USER
    assert command._builder.options[1].type == hikari.OptionType.USER
    assert not command._tracked_options["user"].is_only_member
    assert command._tracked_options["member"].is_only_member


def test_parse_parameter_with_channel():
    command = SlashCommand()

    parse_parameter(command, typing.Union[hikari.GuildVoiceChannel, hikari.GuildStageChannel])

    option = command._builder.options[0]
    assert option.type == hikari.OptionType.CHANNEL
    assert option.channel_types == [hikari.ChannelType.GUILD_VOICE, hikari.ChannelType.GUILD_STAGE]


def test_parse_parameter_with_range():
    command = SlashCommand()

    parse_parameter(command, types.Range(1, 2))
    option = command._builder.options[0]
    assert option.type == hikari.OptionType.INTEGER
    assert option.min_value == 1 and option.max_value == 2

    command = SlashCommand()

    parse_parameter(command, types.Range[0.0, ...])
    option = command._builder.options[0]
    assert option.type == hikari.OptionType.FLOAT
    assert option.min_value == 0 and option.max_value is None


def test_parse_parameter_with_converter():
    command = SlashCommand()

    parse_parameter(command, hikari.KnownCustomEmoji, name="emoji")
    assert command._builder.options[0].type == hikari.OptionType.STRING
    assert command._tracked_options["emoji"].converters[0].__class__ is tanjun.conversion.ToEmoji


def test_parse_parameter_with_converter_class():
    command = SlashCommand()

    parse_parameter(command, types.Converted[int], name="bigint")
    assert command._builder.options[0].type == hikari.OptionType.STRING
    assert command._tracked_options["bigint"].converters == [int]

    command = SlashCommand()

    parse_parameter(command, types.Converted[int, round], name="bigint")
    assert command._builder.options[0].type == hikari.OptionType.STRING
    assert command._tracked_options["bigint"].converters == [round]


def test_parse_parameter_with_annotated_class():
    command = SlashCommand()

    autocomplete = mock.Mock()

    parse_parameter(command, types.Autocompleted[autocomplete])
    assert command._builder.options[0].type == hikari.OptionType.STRING
    assert command._str_autocompletes["option"].__wrapped__ == autocomplete
    assert not command._tracked_options["option"].converters

    command = SlashCommand()

    parse_parameter(command, types.Autocompleted[autocomplete, int])
    assert command._builder.options[0].type == hikari.OptionType.STRING
    assert command._str_autocompletes["option"].__wrapped__ == autocomplete
    assert command._tracked_options["option"].converters == [int]


def test_parse_parameter_with_misc():
    command = SlashCommand()

    with pytest.raises(TypeError):
        parse_parameter(command, annotation=object())
