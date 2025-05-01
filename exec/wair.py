#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from collections import Counter, defaultdict
from glob import glob

import redis

from utils import fs, recluster, rss, stats

cap = int(sys.argv[1]) if len(sys.argv) > 1 else 200

r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

ratios = defaultdict(dict)
paths = glob('stats/*.json')
paths.sort(key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))
for stats_file in paths:
    nr = int(os.path.splitext(os.path.basename(stats_file))[0])

    _, io_time, projs, _ = stats(stats_file)

    fs_file = stats_file.removesuffix('.json') + '.txt'
    (gets, puts), httpfs = fs(fs_file)
    io_k = (gets + puts) / io_time

    rss_file = stats_file.removesuffix('.json') + '.bin'
    result_set_sizes = rss(rss_file)
    files = sorted(result_set_sizes.keys(),
                   key=lambda x: int(os.path.splitext(x)[0]))

    pipe = r.pipeline()
    for file in files:
        for column in projs:
            pipe.hget(f'{file}:{column}', 'total_uncompressed_size')
            pipe.hget(f'{file}:{column}', 'compression_ratio')
    data = pipe.execute()

    for i, file in enumerate(files):
        total, used = 0, 0
        for j, column in enumerate(projs):
            total_uncompressed_size = int(data[i * len(projs) * 2 + j * 2])
            compression_ratio = float(data[i * len(projs) * 2 + j * 2 + 1])
            total += total_uncompressed_size * compression_ratio
            used += result_set_sizes[file][column] * compression_ratio
        if used not in (None, 0, total):
            ratios[file][nr] = (used, total), httpfs[file], io_k

hits = {file: sum((total - hit) / total * size / io_k for (hit, total), size, io_k in hits.values())
        for file, hits in ratios.items()}

hits = {filename: metric for filename,
        metric in hits.items() if 3 * metric > 1}

for file, hit in hits.items():
    print(file, hit, file=sys.stderr)

files, metrics = zip(*Counter(hits).most_common()[:cap])
recluster(files)
