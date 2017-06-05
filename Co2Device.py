# -*- coding: utf-8 -*-

from __future__ import print_function

import fcntl
from collections import namedtuple

# based on code by henryk ploetz
# https://hackaday.io/project/5301-reverse-engineering-a-low-cost-usb-co-monitor/log/17909-all-your-base-are-belong-to-us


EnvironmentData = namedtuple("EnvironmentData", ["temperature", "co2_level"])


def hex_format(d):
    return " ".join("%02X" % e for e in d)


class Co2Device(object):

    def __init__(self, device_path):
        self._device_path = device_path
        self._values = {}
        self._device_key = [0xc4, 0xc6, 0xc0, 0x92, 0x40, 0x23, 0xdc, 0x96]

    def decrypt(self, data):
        cstate = [0x48, 0x74, 0x65, 0x6D, 0x70, 0x39, 0x39, 0x65]
        shuffle = [2, 4, 0, 7, 1, 6, 5, 3]

        phase1 = [0] * 8
        for i, o in enumerate(shuffle):
            phase1[o] = data[i]

        phase2 = [0] * 8
        for i in range(8):
            phase2[i] = phase1[i] ^ self._device_key[i]

        phase3 = [0] * 8
        for i in range(8):
            phase3[i] = ((phase2[i] >> 3) | (phase2[(i - 1 + 8) % 8] << 5)) & 0xff

        ctmp = [0] * 8
        for i in range(8):
            ctmp[i] = ((cstate[i] >> 4) | (cstate[i] << 4)) & 0xff

        out = [0] * 8
        for i in range(8):
            out[i] = (0x100 + phase3[i] - ctmp[i]) & 0xff

        return out

    def open_monitor_device(self):
        self._co2_monitor_device_handle = open(self._device_path, "a+b", 0)
        HIDIOCSFEATURE_9 = 0xC0094806
        set_report = "\x00" + "".join(chr(e) for e in self._device_key)
        fcntl.ioctl(self._co2_monitor_device_handle, HIDIOCSFEATURE_9, set_report)

    def read_device_data(self):
        data = list(ord(chunk) for chunk in self._co2_monitor_device_handle.read(8))
        decrypted = self.decrypt(data)

        if decrypted[4] != 0x0d or (sum(decrypted[:3]) & 0xff) != decrypted[3]:
            print(hex_format(data), " => ", hex_format(decrypted), "Checksum error")
        else:
            op = decrypted[0]
            val = decrypted[1] << 8 | decrypted[2]
            self._values[op] = val

            if (0x50 in self._values) and (0x42 in self._values):
                co2_level = self._values[0x50]
                temperature = (self._values[0x42] / 16.0 - 273.15)
                if not (co2_level > 5000 or co2_level < 0):
                    return EnvironmentData(co2_level=co2_level, temperature=temperature)

        return None
