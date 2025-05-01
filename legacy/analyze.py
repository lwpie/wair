#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import operator
import os
import sys
from collections import defaultdict
from glob import glob

import duckdb
from tqdm import tqdm

from utils import PREFIX, fs, stats

if __name__ == '__main__':
    with open('files.txt', encoding='utf-8') as f:
        files = f.read().splitlines()
    if not files:
        sys.exit(0)

    io_times = defaultdict(dict)
    reduces = defaultdict(int)
    for stats_file in tqdm(glob('stats/[!r]*.json')):
        nr = int(os.path.splitext(os.path.basename(stats_file))[0])

        _, io_time, _, filters = stats(stats_file)
        fs_file = stats_file.removesuffix('.json') + '.txt'
        (gets, puts), httpfs = fs(fs_file)
        io = io_time / (gets + puts)

        total = 0
        for filename in files:
            if filename in httpfs:
                io_times[filename][nr] = httpfs[filename] * io
                total += httpfs[filename]
                hit = duckdb.sql(
                    f"SELECT COUNT(*) FROM '{os.path.join(PREFIX, filename)}' WHERE {' AND '.join(filters)};").fetchone()[0]
                if not hit:
                    reduces[nr] += httpfs[filename]

        if not total:
            continue
        reduces[nr] /= total
        for v in io_times.values():
            if nr in v:
                v[nr] *= reduces[nr]

    io_times = {k: sum(v.values()) for k, v in io_times.items()}
    for filename, io_time in sorted(io_times.items(), key=operator.itemgetter(1), reverse=True):
        print(filename, io_time, file=sys.stderr)

    r_time, _, _, _ = stats('stats/r.json')
    # print(r_time)
