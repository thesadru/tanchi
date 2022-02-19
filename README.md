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

---

## Documentation?

### Ordinary Types

All builtin types supported in slash commands (`str`, `int`, `float`, `bool`) do not need any special care.

```py
option: str
```

### Choices

Choices can either be made with `typing.Literal` or `enum.Enum`

```py
option: typing.Literal["Foo", "Bar", "Baz"]
```

```py
class MyEnum(enum.IntEnum):
    foo = 1
    bar = 2
    baz = 3

option: MyEnum
```

## Users

Tanchi makes no distinction between the different types of users, but tanjun enforces `hikari.Member` at runtime.

```py
option: hikari.Member
```

### Channels

Channels types may be enforced with the help of `typing.Union`. If you want all channel types use `hikari.GuildChannel`

```py
option: typing.Union[hikari.GuildTextChannel, hikari.GuildNewsChannel]
```

### Docstrings

Tanchi parses descriptions from docstrings.

Examples of all supported formats:

#### ReST

```py
"""Command description on a single line

Parameters
----------
foo : OptionType
    Description for the option named "foo"
bar:
    Description for the option named "bar"
"""
```
