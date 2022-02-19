import typing

import hikari
import pytest
import tanjun

from tanchi import commands, types


def test_as_slash_command():
    @commands.as_slash_command()
    async def command(
        context: tanjun.context.SlashContext,
        number: types.Range[0, 1.0],
        choices: typing.Literal[1, 2, 3],
        member: hikari.Member = None,
        channel: typing.Union[hikari.GuildTextChannel, hikari.GuildNewsChannel] = None,
        *,
        injection: hikari.RESTAware = tanjun.inject(type=hikari.RESTAware),
    ):
        """Command description.

        Parameters
        ----------
        number : float
            A number
        choices : int
            Anything picked from the choices
        member : hikari.Member
            A member, runtime enforced
        channel : hikari.GuildTextChannel | hikari.GuildNewsChannel
            A text or news channel, very cool!
        """

    builder = command.build()
    assert builder.name == "command"
    assert builder.description == "Command description."

    assert len(builder.options) == 4
    assert builder.options[0] == hikari.CommandOption(
        type=hikari.OptionType.FLOAT,
        name="number",
        description="A number",
        is_required=True,
        min_value=0,
        max_value=1.0,
    )
    assert builder.options[1] == hikari.CommandOption(
        type=hikari.OptionType.INTEGER,
        name="choices",
        description="Anything picked from the choices",
        is_required=True,
        choices=[
            hikari.CommandChoice(name="1", value=1),
            hikari.CommandChoice(name="2", value=2),
            hikari.CommandChoice(name="3", value=3),
        ],
    )
    assert builder.options[2] == hikari.CommandOption(
        type=hikari.OptionType.USER,
        name="member",
        description="A member, runtime enforced",
    )
    assert builder.options[3] == hikari.CommandOption(
        type=hikari.OptionType.CHANNEL,
        name="channel",
        description="A text or news channel, very cool!",
        channel_types=[hikari.ChannelType.GUILD_TEXT, hikari.ChannelType.GUILD_NEWS],
    )


def test_missing_docstring():
    with pytest.raises(TypeError):

        @commands.as_slash_command()
        async def missing_docstring(context: tanjun.context.SlashContext):
            pass
