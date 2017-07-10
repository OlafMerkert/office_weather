from __future__ import print_function

import sys
from datetime import datetime
from Co2Device import Co2Device

with open("/tmp/co2datalog.csv", "a") as logfile:
    def logger(op_code, value):
        logfile.write("{0}, {1}, {2},\n".format(
            datetime.now().time(),
            op_code,
            value,
        ))

    device = Co2Device(sys.argv[1], logger)
    device.open_monitor_device()

    while True:
        data = device.read_device_data()
        print("debug current data: {0}".format(data))
