import enum
import inspect
import typing
from unittest import mock

import hikari
import pytest
import tanjun

from tanchi import conversion, parser, types


def parse_parameter(
    command: tanjun.SlashCommand[typing.Any],
    annotation: typing.Any,
    *,
    default: typing.Any = types.UNDEFINED_DEFAULT,
) -> None:
    parser.parse_parameter(
        command,
        name="name",
        annotation=annotation,
        default=default,
    )


def assert_called_with(
    func: mock.Mock,
    *args: typing.Any,
    **kwargs: typing.Any,
) -> None:
    call_args: typing.Sequence[typing.Any] = func.call_args.args
    for value in args:
        assert value in call_args, f"Expected {mock._Call((args, kwargs))!r} but called with {func.call_args!r}"

    call_kwargs: typing.Mapping[str, typing.Any] = func.call_args.kwargs
    for key, value in kwargs.items():
        assert key in call_kwargs, f"{func} was not called with a parameter called {key!r}"
        assert call_kwargs[key] == value, f"Expected {mock._Call((args, kwargs))!r} but called with {func.call_args!r}"


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

    parse_parameter(command, int)

    assert_called_with(
        command._add_option,
        hikari.OptionType.INTEGER,
        min_value=None,
        max_value=None,
    )


def test_parse_parameter_with_string_choices():
    command = mock.Mock(tanjun.SlashCommand)

    parse_parameter(command, typing.Literal["A", "B", "C"])

    assert_called_with(
        command._add_option,
        hikari.OptionType.STRING,
        choices={"A": "A", "B": "B", "C": "C"},
    )


def test_parse_parameter_with_user():
    command = mock.Mock(tanjun.SlashCommand)

    parse_parameter(command, hikari.User)
    command.add_user_option.assert_called()

    parse_parameter(command, hikari.InteractionMember)
    command.add_member_option.assert_called()


def test_parse_parameter_with_channel():
    command = mock.Mock(tanjun.SlashCommand)

    parse_parameter(command, typing.Union[hikari.GuildVoiceChannel, hikari.GuildStageChannel])

    assert_called_with(
        command.add_channel_option,
        types=[hikari.GuildVoiceChannel, hikari.GuildStageChannel],
    )


def test_parse_parameter_with_range():
    command = mock.Mock(tanjun.SlashCommand)

    parse_parameter(command, types.Range(1, 2))
    assert_called_with(
        command._add_option,
        hikari.OptionType.INTEGER,
        min_value=1,
        max_value=2,
    )

    command = mock.Mock(tanjun.SlashCommand)

    parse_parameter(command, types.Range(0, 1.0))
    assert_called_with(
        command._add_option,
        hikari.OptionType.FLOAT,
        min_value=0,
        max_value=1.0,
    )


def test_parse_parameter_with_converter():
    command = mock.Mock(tanjun.SlashCommand)

    parse_parameter(command, hikari.KnownCustomEmoji)

    assert_called_with(
        command.add_str_option,
        converters=[mock.ANY],
    )
    converter = command.add_str_option.call_args.kwargs["converters"][0]
    assert isinstance(converter, tanjun.conversion.ToEmoji)


def test_parse_parameter_with_converter_class():
    command = mock.Mock(tanjun.SlashCommand)

    parse_parameter(command, types.Converted[int])
    assert_called_with(
        command.add_str_option,
        converters=[mock.ANY],
    )
    converter = command.add_str_option.call_args.kwargs["converters"][0]
    assert converter == int

    command = mock.Mock(tanjun.SlashCommand)

    parse_parameter(command, types.Converted[int, round])
    assert_called_with(
        command.add_str_option,
        converters=[mock.ANY],
    )
    converter = command.add_str_option.call_args.kwargs["converters"][0]
    assert converter == round


def test_parse_parameter_with_misc():
    command = mock.Mock(tanjun.SlashCommand)

    with pytest.raises(TypeError):
        parse_parameter(command, annotation=object())
