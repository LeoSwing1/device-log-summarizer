import tempfile
import unittest
from pathlib import Path

from main import clean_sensor_readings, summarize_csv


class CleanSensorReadingsTests(unittest.TestCase):
    def test_filters_and_caps(self):
        self.assertEqual(
            clean_sensor_readings([12, "4.5", None, -1, "bad", 900]),
            [12.0, 4.5, 500.0],
        )

    def test_empty_and_all_invalid(self):
        self.assertEqual(clean_sensor_readings([]), [])
        self.assertEqual(clean_sensor_readings([None, "x", -4]), [])

    def test_zero_is_valid(self):
        self.assertEqual(clean_sensor_readings([0, "0"]), [0.0, 0.0])


class SummarizeCsvTests(unittest.TestCase):
    def test_aggregates_and_filters_hot_devices(self):
        content = (
            "device_id,status,temperature\n"
            "DEV_A,ACTIVE,40\n"
            "DEV_A,ERROR,60\n"
            "DEV_B,ERROR,90\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.csv"
            path.write_text(content, encoding="utf-8")
            result = summarize_csv(path)
        self.assertEqual(result, [{
            "device_id": "DEV_A",
            "total_records": 2,
            "average_temperature": 50.0,
            "error_count": 1,
        }])

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            summarize_csv(Path("does-not-exist.csv"))


if __name__ == "__main__":
    unittest.main()
