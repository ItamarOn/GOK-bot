from datetime import datetime, timezone
from utils.time_check import is_night_hours

def test_is_night_hours_daytime():
    # 12/1/2026 5 PM in jerusalem (UTC+2) by unix seconds:
    ts = int(datetime(2026, 1, 12, 15, 0, 0,
                       tzinfo=timezone.utc).timestamp())
    assert not is_night_hours(ts)


def test_is_night_hours_nighttime():
    # 12/1/2026 3 AM in jerusalem (UTC+2) by unix seconds:
    ts = int(datetime(2026, 1, 12, 1, 0, 0,
                       tzinfo=timezone.utc).timestamp())
    assert is_night_hours(ts)