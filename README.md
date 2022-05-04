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
        Any integer value.
    flag : bool
        Whether this flag should be enabled.
    channel : hikari.GuildTextChannel
        The channel to target.
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

### Ranges

Integer and float options support min and max boundaries. These can be set with `tanchi.Range`.
The type of the option is discerned from the boundaries.

```py
int_option: tanchi.Range[1, 10]
float_option: tanchi.Range[0.0, 1.0]
```

### Channels

Channels types may be enforced with the help of `typing.Union`. If you want all channel types use `hikari.GuildChannel`

```py
option: typing.Union[hikari.GuildTextChannel, hikari.GuildNewsChannel]
```

### Converters

Types are implicitly converted if a builtin tanjun converter is available.

```py
option: hikari.Emoji
```

To provide your own converter you can use `tanchi.Converted`.

```py
option: tanchi.Converted[int, round]
```

### Autocomplete

Instead of using a decorator, autocompleters can be provided directly in the annotation with `tanchi.Autocompleted`.

```py
option: tanchi.Autocompleted[autocomplete_callback]
```

Since converters and autocompletion are often used together you can provide a converter directly.

```py
option: tanchi.Autocompleted[autocomplete_callback, converter_callback]
```

### MyPy compatibility

Because mypy does not respect `__class_getitem__` you'll most likely have to use `typing.Annotated` for some cases.

```py
option: typing.Annotated[int, tanchi.Range(1, 10)]
option: typing.Annotated[int, tanchi.Converted(range)]
option: typing.Annotated[str, tanchi.Autocompleted(autocomplete_callback)]
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

#### Google

```py
"""Command description on a single line

Args:
    foo (OptionType): Description for the option named "foo"
    bar: Description for the option named "bar"
"""
```

## Autocompletion Examples

Instead of using `context.set_choices` you can choose to return options as either a sequence or a mapping.

```py
@tanchi.as_slash_command()
async def command(context: tanjun.abc.SlashContext, option: str) -> None:
    ...

@tanchi.with_autocomplete(command, "option")
def autocomplete_names(context: tanjun.abc.AutocompleteContext, option: str):
    return [word for word in WORDS if option.lower() in word.lower()]
```

Returning the options is also supported inside [`Autocompleted`](#autocomplete)
