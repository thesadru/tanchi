import datetime

import hikari
import pytest

from tanchi import conversion


def test_to_snowflake():
    converter = conversion.ToSnowflake()
    assert converter.__call__("454513969265115137") == hikari.Snowflake(454513969265115137)

    assert not any((converter.async_caches, converter.cache_components, converter.intents, converter.requires_cache))


def test_to_datetime():
    converter = conversion.ToDatetime()
    assert converter("<t:297388800:R>") == datetime.datetime(1979, 6, 5, tzinfo=datetime.timezone.utc)

    iso = "2001-09-11T00:46:00+00:00"
    assert converter(iso) == datetime.datetime(2001, 9, 11, 00, 46, tzinfo=datetime.timezone.utc)

    with pytest.raises(ValueError):
        converter("invalid")
