#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import multiprocessing as mp
import os
import sys
from collections import Counter, defaultdict
from glob import glob

import duckdb
from tqdm import tqdm

from utils import PREFIX, fs, recluster, sizeof, stats

if __name__ == '__main__':
    cap = int(sys.argv[1]) if len(sys.argv) > 1 else 200

    dyn = defaultdict(dict)
    for stats_file in tqdm(sorted(glob('stats/*.json'), key=lambda x: int(os.path.splitext(os.path.basename(x))[0])), leave=False):
        nr = int(os.path.splitext(os.path.basename(stats_file))[0])

        _, io_time, projs, filters = stats(stats_file)

        fs_file = stats_file.removesuffix('.json') + '.txt'
        (gets, puts), httpfs = fs(fs_file)
        io_k = (gets + puts) / io_time
        files, sizes = zip(*httpfs.items())

        def query(filename):
            cols = ' + '.join(
                f'SUM({sizeof(col, filename)})' for col in projs)
            hit = duckdb.sql(
                f"SELECT {cols} FROM '{os.path.join(PREFIX, filename)}' WHERE {' AND '.join(filters)};").fetchone()[0]
            total = duckdb.sql(
                f"SELECT {cols} FROM '{os.path.join(PREFIX, filename)}';").fetchone()[0]
            return None if hit in (None, 0, total) else (float(hit), float(total))

        with mp.Pool() as pool:
            hits = pool.map(query, files)

        for filename, hit, size in zip(files, hits, sizes):
            if hit is not None:
                dyn[filename][nr] = (hit, size, io_k)

    hits = {filename: sum((total - hit) / total * size / io_k for (hit, total), size, io_k in hits.values())
            for filename, hits in dyn.items()}
    # for filename, metric in Counter({filename: sum(metric) for filename, metric in hits.items()}).most_common():
    #     print(filename, hits[filename], file=sys.stderr)
    hits = {filename: metric for filename,
            metric in hits.items() if 9 * metric > 1}

    if hits:
        files, metrics = zip(*Counter(hits).most_common()[:cap])
        for filename, hit in zip(files, metrics):
            print(filename, hit, file=sys.stderr)
        recluster(files)
    else:
        recluster(None)
