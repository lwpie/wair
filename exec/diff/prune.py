#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import multiprocessing as mp
import os
import re
from glob import glob

import duckdb
from tqdm import tqdm

from utils import SCHEMA

PREFIX = 'pool/lineitem'

with open('explain.json', encoding='utf-8') as f:
    nodes = json.load(f)

filters = list()
while nodes:
    node = nodes.pop(0)
    if node['name'].strip() in ('PARQUET_SCAN', 'READ_PARQUET'):
        if _filter := node['extra_info'].get('Filters'):
            filters.extend(_filter if isinstance(
                _filter, list) else [_filter])
    nodes.extend(node['children'])

filters = sorted(filter(lambda x: any(
    col in x for col in SCHEMA), set(filters)))
# print('\n'.join(filters), file=sys.stderr)

if __name__ == '__main__':
    def prune(file):
        for _filter in filters:
            outcome = duckdb.sql(
                f"SELECT COUNT(*) > 0 FROM '{os.path.join(PREFIX, file)}' WHERE {_filter};"
            ).fetchall()[0][0]
            if not outcome:
                return file, False
        return file, True

    with mp.Pool() as pool:
        outcomes = dict(tqdm(pool.imap_unordered(prune, files),
                        total=len(files), leave=False))

    # print(sum(outcomes.values()), len(files), file=sys.stderr)
    files = sorted([file for file, outcome in outcomes.items()
                   if outcome], key=lambda x: int(os.path.splitext(x)[0]))

    with open('pruned.txt', encoding='utf-8') as f:
        data = f.read().strip()

    outcomes = re.findall(r'/(\d+.parquet)', data)
    if set(outcomes) == set(files):
        print('Identical')
    else:
        print(set(outcomes) - set(files))
        print(set(files) - set(outcomes))
