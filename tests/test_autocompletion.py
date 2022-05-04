from unittest import mock

import hikari
import pytest
import tanjun

from tanchi import autocompletion


@pytest.fixture
def client():
    return tanjun.Client.from_gateway_bot(mock.Mock())


@pytest.mark.asyncio
async def test_autocompletion(client: tanjun.Client):
    command = tanjun.SlashCommand(mock.Mock(), "name", "description")
    command.add_str_option("string", "cool string")

    @autocompletion.with_autocomplete(command, "string")
    def callback(context: tanjun.abc.AutocompleteContext, argument: str):
        return ["A", "B", "C", argument]

    interaction = mock.AsyncMock()
    interaction.options = [
        hikari.AutocompleteInteractionOption(
            name="string",
            type=hikari.OptionType.STRING,
            value="AAAAA",
            options=None,
            is_focused=True,
        )
    ]
    context = tanjun.context.AutocompleteContext(client, interaction)
    assert context.focused.name == "string"

    await command.execute_autocomplete(context)

    expected = [hikari.CommandChoice(name=value, value=value) for value in ("A", "B", "C", "AAAAA")]
    interaction.create_response.assert_awaited_once_with(expected)
