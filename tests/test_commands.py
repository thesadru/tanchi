import typing

import hikari
import pytest
import tanjun

from tanchi import commands


def test_as_slash_command():
    @commands.as_slash_command()
    async def command(
        context: tanjun.context.SlashContext,
        number: float,
        choices: typing.Literal[1, 2, 3],
        member: hikari.Member,
        injection=tanjun.inject(type=hikari.RESTAware),
        channel: typing.Union[hikari.GuildTextChannel, hikari.GuildNewsChannel] = None,
    ):
        """command description

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

    assert command.name == "command"


def test_missing_docstring():
    with pytest.raises(TypeError):

        @commands.as_slash_command()
        async def missing_docstring(context: tanjun.context.SlashContext):
            pass
