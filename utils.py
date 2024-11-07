import logging
from datetime import datetime

logger = logging.getLogger()


def normalize_num(num, nums):
    try:
        return num / max(nums)
    except:
        print(f"Error normalizing {num} with {nums}")


def calculate_remaining_work_hours(start_datetime, end_datetime, schedule):

    if start_datetime > end_datetime:
        return 0

    total_working_hours = 0
    for period in schedule:
        period_start = datetime.fromisoformat(period["startDate"])
        period_end = datetime.fromisoformat(period["endDate"])
        # if start of the period is after breach date or end of the period is before now, skip period.
        if period_start > end_datetime or period_end < start_datetime:
            continue
        total_working_hours += (
            min(period_end, end_datetime) - max(period_start, start_datetime)
        ).seconds / 3600

    return total_working_hours
