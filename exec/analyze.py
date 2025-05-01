#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from glob import glob

from tqdm import tqdm

from utils import fs, parse, stats

base = sys.argv[1]

cpu_times = list()
io_times = list()
io_sizes = list()
r_cpu_times = list()
r_io_times = list()
r_io_sizes = list()
for path in tqdm(sorted(filter(os.path.isdir, glob(os.path.join(base, '*'))), key=lambda x: int(os.path.basename(x)))):
    cpu_time = list()
    io_time = list()
    io_size = list()
    r_cpu_time = list()
    r_io_time = list()
    r_io_size = list()
    for stats_file in glob(os.path.join(path, '*.json')):
        nr = os.path.splitext(os.path.basename(stats_file))[0]
        _cpu_time, _io_time, _, _ = stats(stats_file)

        fs_file = stats_file.removesuffix('.json') + '.txt'
        (gets, puts), _ = fs(fs_file)

        cpu_time.append(_cpu_time)
        io_time.append(_io_time)
        io_size.append(gets + puts)

        if nr == 'r':
            r_cpu_time.append(_cpu_time)
            r_io_time.append(_io_time)
            r_io_size.append(gets + puts)

    cpu_times.append(sum(cpu_time))
    io_times.append(sum(io_time))
    io_sizes.append(sum(io_size))
    r_cpu_times.append(sum(r_cpu_time))
    r_io_times.append(sum(r_io_time))
    r_io_sizes.append(sum(r_io_size))

print(sum(cpu_times), sum(io_times), sum(io_sizes))
print(sum(r_cpu_times), sum(r_io_times), sum(r_io_sizes))
print(sum(r_cpu_times) / sum(cpu_times), sum(r_io_times) /
      sum(io_times), sum(r_io_sizes) / sum(io_sizes))
print(parse(base))
