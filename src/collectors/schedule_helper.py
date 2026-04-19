from datetime import datetime, timedelta, time


class ScheduleHelper:
    def seconds_until_next_interval(self, interval_minutes: int) -> float:
        """Returns seconds until the next aligned interval boundary."""
        now = datetime.now()
        remainder = now.minute % interval_minutes
        minutes_to_add = interval_minutes - remainder
        next_run = now.replace(second=0, microsecond=0) + timedelta(minutes=minutes_to_add)
        return (next_run - now).total_seconds()

    def seconds_until_hour(self, hour: int) -> float:
        """Returns seconds until the next occurrence of the given hour (next day if already past)."""
        now = datetime.now()
        next_start = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if now >= next_start:
            next_start += timedelta(days=1)
        return (next_start - now).total_seconds()

    def is_within_hours(self, start_hour: int, end_hour: int) -> bool:
        """Returns True if current local time is between start_hour and end_hour."""
        now = datetime.now().time()
        return time(hour=start_hour) < now < time(hour=end_hour)