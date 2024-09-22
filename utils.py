import logging
from datetime import datetime, timezone, timedelta, time

logger = logging.getLogger()


def normalize_num(num, nums):
    try:
        return num / max(nums)
    except:
        print(f"Error normalizing {num} with {nums}")


def calculate_remaining_work_hours(start_datetime, end_datetime, start_time, end_time):
    # Ensure start_datetime is before end_datetime
    if start_datetime > end_datetime:
        return 0

    total_working_hours = 0
    current_datetime = start_datetime

    while current_datetime <= end_datetime:
        if current_datetime.weekday() < 5:  # Monday to Friday are 0 to 4
            # Calculate the start and end of the work period for the current day
            work_start = datetime.combine(current_datetime.date(), start_time)
            if start_time < end_time:
                work_end = datetime.combine(current_datetime.date(), end_time)
            else:
                work_end = datetime.combine(
                    current_datetime.date() + timedelta(days=1), end_time
                )

            # Adjust the start and end times if they are outside the work period
            if current_datetime > work_start:
                work_start = current_datetime
            if end_datetime < work_end:
                work_end = end_datetime

            # Calculate the working hours for the current day
            if work_start < work_end:
                total_working_hours += (work_end - work_start).seconds / 3600

        # Move to the next day
        current_datetime = datetime.combine(
            current_datetime.date() + timedelta(days=1), time.min
        ).astimezone(timezone.utc)

    return total_working_hours
