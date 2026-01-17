from datetime import datetime, timezone
from config import WORKING_HOURS, tz_info


def is_night_hours(timestamp: int) -> bool:
    """ Return True if the timestamp (unix seconds) is outside working hours """
    start_hour, end_hour = map(int, WORKING_HOURS.split(","))
    now_hour = datetime.fromtimestamp(timestamp, tz=timezone.utc).astimezone(tz_info).hour
    # If start <= hour < end -> working hours -> return False
    return not (start_hour <= now_hour < end_hour)

def is_too_old(timestamp: int, max_age_hours: int = 3) -> bool:
    """ Return True if the timestamp (unix seconds) is older than max_age_seconds """
    max_age_seconds = max_age_hours * 3600
    now_ts = datetime.now(tz=timezone.utc).timestamp()
    return timestamp < (now_ts - max_age_seconds)
