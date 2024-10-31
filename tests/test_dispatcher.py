import unittest
from datetime import datetime, time, timedelta, timezone

from dispatcher import Score


class TestCalculateRemainingWorkHours(unittest.TestCase):
    def setUp(self):
        self.score = Score(None, [])
        self.work_time = {
            "start": time(9, 0, 0).replace(tzinfo=timezone.utc),
            "end": time(17, 0, 0).replace(tzinfo=timezone.utc),
        }
        self.now = datetime(2024, 1, 1, 10, 0, 0, 0).replace(tzinfo=timezone.utc)

    def test_remaining_hours_same_day(self):
        timestamp = self.now.replace(hour=15, minute=0, second=0, microsecond=0)
        remaining_hours = self.score._calculate_remaining_work_hours(
            self.now, timestamp, self.work_time["start"], self.work_time["end"]
        )
        expected_hours = 5  # 17:00 - 15:00
        self.assertAlmostEqual(remaining_hours, expected_hours, places=2)

    def test_remaining_hours_next_day(self):
        timestamp = self.now + timedelta(days=1, hours=4)
        remaining_hours = self.score._calculate_remaining_work_hours(
            self.now, timestamp, self.work_time["start"], self.work_time["end"]
        )
        expected_hours = 12  # 7h today plus 5h tomorrow
        self.assertAlmostEqual(remaining_hours, expected_hours, places=2)

    def test_remaining_hours_multiple_days(self):
        timestamp = self.now + timedelta(days=3, hours=10)
        remaining_hours = self.score._calculate_remaining_work_hours(
            self.now, timestamp, self.work_time["start"], self.work_time["end"]
        )
        expected_hours = 31  # 3 full workdays plus 7h today
        self.assertAlmostEqual(remaining_hours, expected_hours, places=2)

    def test_remaining_hours_weekend(self):
        # Assuming today is Friday
        timestamp = self.now + timedelta(days=7, hours=10)  # Monday
        remaining_hours = self.score._calculate_remaining_work_hours(
            self.now, timestamp, self.work_time["start"], self.work_time["end"]
        )
        print(self.now.weekday(), self.now)
        print(timestamp.weekday(), timestamp)
        expected_hours = (
            47  # From Mon 10 AM to next Monday 8 PM, so 5 full work days plus 7h today
        )
        self.assertAlmostEqual(remaining_hours, expected_hours, places=2)

    def test_remaining_hours_before_work_time(self):
        timestamp = self.now.replace(hour=8, minute=0, second=0, microsecond=0)
        remaining_hours = self.score._calculate_remaining_work_hours(
            self.now, timestamp, self.work_time["start"], self.work_time["end"]
        )
        expected_hours = 0  # Before work start time
        self.assertAlmostEqual(remaining_hours, expected_hours, places=2)

    def test_remaining_hours_same_day_pst(self):
        self.work_time = {
            "start": time(15, 0, 0).replace(tzinfo=timezone.utc),
            "end": time(2, 0, 0).replace(tzinfo=timezone.utc),
        }
        timestamp = self.now.replace(hour=19, minute=0, second=0, microsecond=0)
        remaining_hours = self.score._calculate_remaining_work_hours(
            self.now, timestamp, self.work_time["start"], self.work_time["end"]
        )
        expected_hours = 4  # from 15 to 19
        self.assertAlmostEqual(remaining_hours, expected_hours, places=2)

    def test_remaining_hours_next_day_pst(self):
        self.work_time = {
            "start": time(15, 0, 0).replace(tzinfo=timezone.utc),
            "end": time(2, 0, 0).replace(tzinfo=timezone.utc),
        }
        timestamp = self.now + timedelta(days=1)
        remaining_hours = self.score._calculate_remaining_work_hours(
            self.now, timestamp, self.work_time["start"], self.work_time["end"]
        )
        expected_hours = 11  # from 15 to 2 next day
        self.assertAlmostEqual(remaining_hours, expected_hours, places=2)

    def test_remaining_hours_multiple_days_pst(self):
        self.work_time = {
            "start": time(15, 0, 0).replace(tzinfo=timezone.utc),
            "end": time(2, 0, 0).replace(tzinfo=timezone.utc),
        }
        timestamp = self.now + timedelta(days=2, hours=10)
        remaining_hours = self.score._calculate_remaining_work_hours(
            self.now, timestamp, self.work_time["start"], self.work_time["end"]
        )
        expected_hours = 27  # from 15 to 2 next day
        self.assertAlmostEqual(remaining_hours, expected_hours, places=2)

    def test_remaining_hours_weekend_pst(self):
        self.work_time = {
            "start": time(15, 0, 0).replace(tzinfo=timezone.utc),
            "end": time(2, 0, 0).replace(tzinfo=timezone.utc),
        }
        timestamp = self.now + timedelta(days=7, hours=10)
        print(self.now, timestamp, self.work_time["start"], self.work_time["end"])
        remaining_hours = self.score._calculate_remaining_work_hours(
            self.now, timestamp, self.work_time["start"], self.work_time["end"]
        )
        expected_hours = 60  # from 15 to 2 next day
        self.assertAlmostEqual(remaining_hours, expected_hours, places=2)


if __name__ == "__main__":
    unittest.main()
