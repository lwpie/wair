#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import multiprocessing as mp
import os
import sys
from collections import Counter, defaultdict
from glob import glob

import duckdb
from tqdm import tqdm

from utils import PREFIX, fs, sizeof, stats

if __name__ == '__main__':
    cap = int(sys.argv[1]) if len(sys.argv) > 1 else 100

    dyn = defaultdict(dict)
    for stats_file in tqdm(sorted(glob('stats/*.json'), key=lambda x: int(os.path.splitext(os.path.basename(x))[0])), leave=False):
        nr = int(os.path.splitext(os.path.basename(stats_file))[0])

        _, io_time, projs, filters = stats(stats_file)

        fs_file = stats_file.removesuffix('.json') + '.txt'
        (gets, puts), httpfs = fs(fs_file)
        io_k = (gets + puts) / io_time
        files, sizes = zip(*httpfs.items())

        def query(file):
            cols = ' + '.join(
                f'SUM({sizeof(col, file)})' for col in projs)
            hit = duckdb.sql(
                f"SELECT {cols} FROM '{os.path.join(PREFIX, file)}' WHERE {' AND '.join(filters)};").fetchone()[0]
            total = duckdb.sql(
                f"SELECT {cols} FROM '{os.path.join(PREFIX, file)}';").fetchone()[0]
            return None if hit in (None, 0, total) else (float(hit), float(total))

        with mp.Pool() as pool:
            hits = pool.map(query, files)

        for file, hit, size in zip(files, hits, sizes):
            if hit is not None:
                dyn[file][nr] = (hit, size, io_k)

    hits = {file: sum((total - hit) / total * size / io_k for (hit, total), size, io_k in hits.values())
            for file, hits in dyn.items()}

    files, metrics = zip(*Counter(hits).most_common()[:cap])

    with open('metrics.txt', encoding='utf-8') as f:
        lines = [line.split(' ') for line in f.read().strip().splitlines()]
    data = {file: float(metric) for file, metric in lines}

    for file, metric in hits.items():
        if not math.isclose(data[file], metric, rel_tol=1e-4):
            print(file, metric, data[file], file=sys.stderr)
            exit(1)
    print('Identical')
