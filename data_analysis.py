# -*- coding: utf-8 -*-

from __future__ import print_function

import csv
from datetime import datetime
from collections import namedtuple, defaultdict
from matplotlib import pyplot


LogLine = namedtuple("LogLine", ["timestamp", "op_code", "value"])


def parse_time(time_string):
    return datetime.strptime(time_string, "%H:%M:%S.%f")


with open("co2datalog.csv", "r", newline="") as csvfile:
    data_rows = csv.reader(csvfile)

    def transform_csv_data(row):
        return LogLine(timestamp=parse_time(row[0]),
                       op_code=int(row[1]),
                       value=int(row[2]))

    log_data = list(map(transform_csv_data, data_rows))

print(log_data[0])

def sort_by_op_code(log_data):
    table = defaultdict(list)
    for x in log_data:
        table[x.op_code].append(x)

    return table

log_table = sort_by_op_code(log_data)

print(log_table.keys())

def plot_log_table(log_table):
    pyplot.figure()
    for op_code_table in log_table.values():
        x_data = list(map(lambda x: x.timestamp, op_code_table))
        y_data = list(map(lambda x: x.value, op_code_table))
        pyplot.plot(x_data, y_data, '+',
                    label="{0:x}".format(op_code_table[0].op_code))

    pyplot.legend()
 
def split_log_table(keys, log_table):
    positive_table = {}
    negative_table = {}

    for k, v in log_table.items():
        if k in keys:
            positive_table[k] = v
        else:
            negative_table[k] = v

    return positive_table, negative_table

wiggling_table, other_table = split_log_table([0x71, 0x50], log_table)

# plot_log_table(log_table)

plot_log_table(wiggling_table)
plot_log_table(other_table)


pyplot.show()
