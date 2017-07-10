# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
from collections import namedtuple, deque
from datetime import datetime
from itertools import tee

import fcntl


# based on code by henryk ploetz
# https://hackaday.io/project/5301-reverse-engineering-a-low-cost-usb-co-monitor/log/17909-all-your-base-are-belong-to-us


EnvironmentData = namedtuple("EnvironmentData", ["timestamp", "temperature", "co2_level"])


def hex_format(list_of_integers):
    return " ".join(map(lambda some_int: "0x{0:x}".format(some_int), list_of_integers))

def compose_lists(data_list, index_list):
    return [data_list[i] for i in index_list]


def rotate(data_list, offset):
    data_deque = deque(data_list)
    data_deque.rotate(offset)
    return data_deque

def now():
    return datetime.now()


class Co2Device(object):

    def __init__(self, device_path, logger=None):
        self._device_path = device_path
        self._logger = logger
        self._current_data = EnvironmentData(timestamp=now(), temperature=None, co2_level=None)
        self._unknown_op_codes = set()
        self._device_key = [0xc4, 0xc6, 0xc0, 0x92, 0x40, 0x23, 0xdc, 0x96]

    def decrypt(self, read_data):
        assert len(read_data) == 8

        cipher_state = [0x48, 0x74, 0x65, 0x6D, 0x70, 0x39, 0x39, 0x65]
        shuffle = [2, 4, 0, 7, 1, 6, 5, 3]

        def xor(x, y):
            return x ^ y

        def phase3_transformation(x, y):
            return ((x >> 3) | (y << 5)) & 0xff

        def cipher_transformation(x):
            return ((x >> 4) | (x << 4)) & 0xff

        def phase4_transformation(x, y):
            return (0x100 + x - y) & 0xff

        phase1 = compose_lists(read_data, shuffle)
        phase2 = map(xor, phase1, self._device_key)
        phase2a, phase2b = tee(phase2)
        phase3 = map(phase3_transformation, phase2a, rotate(phase2b, 1))
        cipher_state_transformed = map(cipher_transformation, cipher_state)
        phase4 = map(phase4_transformation, phase3, cipher_state_transformed)

        phase4 = list(phase4)
        assert len(phase4) == 8

        return phase4

    def open_monitor_device(self):
        hid_iocs_feature_9 = 0xC0094806
        set_report = bytes([0x00] + self._device_key)

        self._co2_monitor_device_handle = open(self._device_path, "a+b", 0)
        fcntl.ioctl(self._co2_monitor_device_handle, hid_iocs_feature_9, set_report)

    def verify_checksum(self, decrypted_data):
        return (decrypted_data[4] == 0x0d and
                (sum(decrypted_data[:3]) & 0xff) == decrypted_data[3])

    def handle_op(self, op_code, value):
        known_operations = {
            0x42: self.handle_temperature,
            0x50: self.handle_co2,
            # 0x71: self.handle_co2,
        }
        if self._logger:
            self._logger(op_code, value)

        if op_code in known_operations:
            known_operations[op_code](value)
            return self._current_data
        else:
            self._unknown_op_codes.add(op_code)

    def handle_temperature(self, temperature_raw):
        temperature_celsius = temperature_raw / 16.0 - 273.15
        self._current_data = self._current_data._replace(timestamp=now(),
                                                         temperature=temperature_celsius)

    def handle_co2(self, co2_level):
        if 0 <= co2_level <= 5000:
            self._current_data = self._current_data._replace(timestamp=now(),
                                                             co2_level=co2_level)
        else:
            print("debug co2_level out of range: {0}".format(co2_level))

    def read_device_data(self):
        read_bytes = list(self._co2_monitor_device_handle.read(8))  # list() converts to integers
        decrypted_data = self.decrypt(read_bytes)

        if not self.verify_checksum(decrypted_data):
            print(hex_format(read_bytes), " => ", hex_format(decrypted_data), "Checksum error")
        else:
            op_code = decrypted_data[0]
            value = decrypted_data[1] << 8 | decrypted_data[2]

            return self.handle_op(op_code, value)

        return None


def device_bare_loop(logger=None):
    device = Co2Device(sys.argv[1], logger)
    device.open_monitor_device()

    while True:
        data = device.read_device_data()
        print("debug current data: {0}".format(data))

if __name__ == "__main__":
    device_bare_loop()
