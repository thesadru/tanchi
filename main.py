import datetime
import inspect
import typing
import hikari
import tanchi
import tanjun
import dateparser


def datetime_converter(string: str) -> datetime.datetime:
    if time := dateparser.parse(string):
        return time

    raise ValueError(f"{string} is not a valid time format.")


async def datetime_autocomplete(context: tanjun.context.AutocompleteContext, string: str) -> None:
    parsed = dateparser.parse(string)

    if parsed is None:
        await context.set_choices({"Please enter a valid date": string})
    else:
        await context.set_choices({parsed.isoformat(): parsed.isoformat()})


@tanchi.as_slash_command()
async def command(
    context: tanjun.context.SlashContext,
    time: tanchi.Autocompleted[datetime_autocomplete, (datetime_converter, datetime_converter)],
):
    """Command that autocompletes the time.

    Args:
        time: Any time format.
    """
    print(time)
    await context.respond(str(time))
