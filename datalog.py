from __future__ import print_function

from datetime import datetime
from Co2Device import device_bare_loop


def run_with_logger(logfile, body):
    with open(logfile, "a") as logfile:
        def logger(op_code, value):
            logfile.write("{0}, {1}, {2},\n".format(
                datetime.now().time(),
                op_code,
                value,
            ))

        print("debug start logging data to {0}".format(logfile))

        body(logger)

if __name__ == "__main__":
    run_with_logger("/tmp/co2datalog.csv", device_bare_loop)
