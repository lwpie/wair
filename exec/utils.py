#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from collections import defaultdict
from glob import glob

import duckdb

COL = 'l_shipdate'
S3_PREFIX = os.environ.get('S3_BUCKET')

SCHEMA = {row[0]: row[1] for row in duckdb.sql(
    "DESCRIBE 'pool/lineitem/0.parquet';").fetchall()}


def stats(filename):
    with open(filename, encoding='utf-8') as f:
        data = json.load(f)
    cpu_time = data['cpu_time']

    io_times = list()
    projs = []
    filters = list()
    nodes = data['children']
    while nodes:
        node = nodes.pop(0)
        if node['operator_type'] == 'TABLE_SCAN':
            if node['extra_info'].get('Function') in ('READ_PARQUET', 'PARQUET_SCAN'):
                proj = node['extra_info']['Projections']
                _projs = proj if isinstance(proj, list) else [proj]
                projs.extend(_projs)
                if _projs and all(_proj in SCHEMA for _proj in _projs):
                    io_times.append(node['cpu_time'])
                if _filter := node['extra_info'].get('Filters'):
                    filters.extend(_filter if isinstance(
                        _filter, list) else [_filter])
        nodes.extend(node['children'])

    projs = sorted(filter(lambda x: x in SCHEMA, set(projs)))
    filters = sorted(filter(lambda x: any(
        col in x for col in SCHEMA), set(filters)))
    assert len(io_times) == 1

    return cpu_time, sum(io_times), projs, filters


def fs(filename):
    with open(filename, encoding='utf-8') as f:
        lines = f.read().strip().split('\n')
    get, gets, puts = map(int, lines.pop().split(' '))
    assert not gets or get / gets > 0.99

    totals = {os.path.basename(file): int(total)
              for file, total in map(str.split, lines)}
    return (gets, puts), totals


def rss(filename):
    with open(filename, encoding='utf-8') as f:
        lines = f.read().rstrip().split('\n')
    data = defaultdict(dict)
    for line in lines:
        if line.startswith(' '):
            assert line.endswith('0')
            continue
        file, column, total = line.split(' ')
        if 's3' in file:
            data[os.path.basename(file)][column] = int(total)
    return data


def parse(path):
    filename = os.path.join(path, 'logs.txt')
    with open(filename, encoding='utf-8') as f:
        data = f.read()
    chunks = data.split('nr/20.sql')[1: -1]
    assert len(chunks) == 25

    hits = list()
    for chunk in chunks:
        chunk = chunk.split('nr/1.sql')[0]
        lines = chunk.strip().splitlines()
        if len(lines) < 3:
            hits.append(0)
        else:
            hits.append(int(chunk.strip().splitlines()[1]))

    return hits


def recluster(files):
    files = sorted(files, key=lambda x: int(os.path.splitext(x)[0]))
    print(len(files))

    with open('src.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(files))

    s3_path = ','.join(
        f"'{os.path.join(S3_PREFIX, filename)}'" for filename in files)
    sql = f"COPY (FROM read_parquet([{s3_path}]) ORDER BY {COL}) TO '{os.path.join(S3_PREFIX, 'r.parquet')}';"
    with open('r.sql', 'w', encoding='utf-8') as f:
        f.write(sql)
