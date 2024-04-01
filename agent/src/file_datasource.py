from csv import reader
from datetime import datetime
from domain.accelerometer import Accelerometer
from domain.gps import Gps
from domain.aggregated_data import AggregatedData
import config


class FileDatasource:
    def __init__(self, accelerometer_filename: str, gps_filename: str) -> None:
        self.accelerometer_filename = accelerometer_filename
        self.gps_filename = gps_filename
        self._position = 0
        self._data = []

    def _smooth_gps(self, gps_generator):
        """
        Smooths GPS coordinates using linear interpolation.
        """
        smooth_step = 5

        for gps_point in gps_generator:
            longitude1, latitude1 = map(float, gps_point)
            yield longitude1, latitude1

            for p2 in gps_generator:
                longitude2, latitude2 = map(float, p2)

                for i in range(1, smooth_step):
                    smoothed_longitude = longitude1 + (longitude2 - longitude1) * i / smooth_step
                    smoothed_latitude = latitude1 + (latitude2 - latitude1) * i / smooth_step
                    yield smoothed_longitude, smoothed_latitude

                longitude1, latitude1 = longitude2, latitude2
                break

    def read(self) -> AggregatedData:
        """Reads and returns the next aggregated data entry."""
        if self._position == len(self._data):
            self._position = 0

        data = self._data[self._position]
        self._position += 1
        return data

    def start_reading(self):
        """Read data from accelerometer and GPS files, aggregate them, and store in _data."""
        self._position = 0
        self._data = []

        with open(self.accelerometer_filename, "r") as accelerometer_file, \
                open(self.gps_filename, "r") as gps_file:

            accelerometer_data_reader = reader(accelerometer_file)
            gps_data_reader = reader(gps_file)
            next(accelerometer_data_reader)
            next(gps_data_reader)

            for accelerometer_row, gps_row in zip(accelerometer_data_reader, self._smooth_gps(gps_data_reader)):
                if not accelerometer_row or not gps_row:
                    continue

                x, y, z = map(int, accelerometer_row)
                longitude, latitude = map(float, gps_row)

                aggregated_data = AggregatedData(
                    config.USER_ID,
                    Accelerometer(x, y, z),
                    Gps(longitude, latitude),
                    datetime.now(),
                )

                self._data.append(aggregated_data)

    def stop_reading(self):
        pass
