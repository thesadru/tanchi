import datetime

from tanchi import conversion


def test_to_datetime():
    converter = conversion.ToDatetime()
    assert converter("<t:297388800:R>") == datetime.datetime(1979, 6, 5, tzinfo=datetime.timezone.utc)

    iso = "2001-09-11T00:46:00+00:00"
    assert converter(iso) == datetime.datetime(2001, 9, 11, 00, 46, tzinfo=datetime.timezone.utc)
