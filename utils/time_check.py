# python
# File: app/utils/time_check.py

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from config import WORKING_HOURS

def unix_timestamp_to_local_hour(timestamp: int, tz_name: str = "Asia/Jerusalem") -> int:
    """ Convert a unix timestamp (seconds) to local hour in the given tz, Returns the hour (0-23) """
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc).astimezone(ZoneInfo(tz_name))
    return dt.hour


def is_night_hours(timestamp: int, tz_name: str = "Asia/Jerusalem") -> bool:
    """ Return True if the timestamp (unix seconds) is outside working hours """
    start_hour, end_hour = map(int, WORKING_HOURS.split(","))
    hour = unix_timestamp_to_local_hour(timestamp, tz_name=tz_name)
    # If start <= hour < end -> working hours -> return False
    return not (start_hour <= hour < end_hour)
