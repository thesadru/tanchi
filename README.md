# tanchi
A signature parser for [hikari](https://github.com/hikari-py/hikari)'s command handler [tanjun](https://github.com/FasterSpeeding/tanjun).

Finally be able to define your commands without those bloody decorator chains!

## Example
```py
@component.with_slash_command
@tanchi.as_slash_command(default_to_ephemeral=True)
async def command(
    ctx: tanjun.abc.SlashContext,
    integer: int = 0,
    flag: bool = False,
    channel: typing.Optional[hikari.GuildTextChannel] = None,
):
    """Small tanchi command
    
    Parameters
    ----------
    integer : int
        Int value.
    flag : bool
        Whether this flag should be enabled
    channel : hikari.GuildTextChannel
        channel to target.
    """
```

