from datetime import datetime, timezone, timedelta
from config import WORKING_HOURS, tz_info
from utils.texts import TEXTS

def is_night_hours(timestamp: int) -> str:
    """ Return True if the timestamp (unix seconds) is outside working hours """
    start_hour, end_hour = map(int, WORKING_HOURS.split(","))
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc).astimezone(tz_info)
    now_hour = dt.hour
    # If start <= hour < end -> working hours -> return False
    is_working_hours = start_hour <= now_hour < end_hour
    if is_working_hours:
        return ""

    if now_hour >= end_hour:
        # If it's late night, morning is tomorrow
        morning_dt = (dt + timedelta(days=1)).replace(
            hour=start_hour, minute=0, second=0, microsecond=0
        )
    else:
        # If it's early morning, morning is today
        morning_dt = dt.replace(
            hour=start_hour, minute=0, second=0, microsecond=0
        )

    # Calculate the difference
    diff = morning_dt - dt
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    lt = TEXTS["left_time"]
    if hours < 1:
        if minutes < 10:
            night_left_str = lt["moments"]
        else:
            night_left_str = lt["minutes_only"].format(minutes=minutes)
    elif hours < 2:
        if minutes < 10:
            night_left_str = lt["hour_only"]
        else:
            night_left_str = lt["hour_and_minutes"].format(minutes=minutes)
    else:
        if minutes < 21:
            night_left_str = lt["hours_only"].format(hours=hours)
        elif minutes > 39:
            night_left_str = lt["next_hour"].format(next_hours=hours + 1)
        else:
            night_left_str = lt["hours_and_half"].format(hours=hours)

    return night_left_str


def is_too_old(timestamp: int, max_age_hours: int = 3) -> bool:
    """ Return True if the timestamp (unix seconds) is older than max_age_seconds """
    max_age_seconds = max_age_hours * 3600
    now_ts = datetime.now(tz=timezone.utc).timestamp()
    return timestamp < (now_ts - max_age_seconds)
