#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
from collections import defaultdict
from glob import glob

import numpy as np
from tqdm import tqdm

SCHEMA = ['l_orderkey', 'l_partkey', 'l_suppkey', 'l_linenumber', 'l_quantity', 'l_extendedprice', 'l_discount', 'l_tax',
          'l_returnflag', 'l_linestatus', 'l_shipdate', 'l_commitdate', 'l_receiptdate', 'l_shipinstruct', 'l_shipmode', 'l_comment']


def stats(filename):
    with open(filename, encoding='utf-8') as f:
        data = json.load(f)
    cpu_time = data['cpu_time']

    io_times = list()
    nodes = data['children']
    while nodes:
        node = nodes.pop(0)
        if node['operator_type'] == 'TABLE_SCAN':
            if node['extra_info'].get('Function') in ('READ_PARQUET', 'PARQUET_SCAN'):
                proj = node['extra_info']['Projections']
                _projs = proj if isinstance(proj, list) else [proj]
                if _projs and all(_proj in SCHEMA for _proj in _projs):
                    io_times.append(node['cpu_time'])
        nodes.extend(node['children'])

    assert len(io_times) == 1
    return cpu_time, sum(io_times)


def fs(filename):
    with open(filename, encoding='utf-8') as f:
        lines = f.read().strip().split('\n')
    get, gets, puts = map(int, lines.pop().split(' '))
    assert not gets or get / gets > 0.99

    return gets, puts


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


def analyze(base):
    assert os.path.isdir(base)
    paths = list(filter(os.path.isdir, glob(os.path.join(base, '*'))))
    paths.sort(key=lambda x: int(os.path.basename(x)))

    cpu_times = defaultdict(dict)
    io_times = defaultdict(dict)
    io_sizes = defaultdict(dict)
    for path in tqdm(paths, leave=False):
        nq = int(os.path.basename(path))
        for stats_file in sorted(glob(os.path.join(path, '*.json'))):
            nr = os.path.splitext(os.path.basename(stats_file))[0]
            cpu_time, io_time = stats(stats_file)

            fs_file = stats_file.removesuffix('.json') + '.txt'
            gets, puts = fs(fs_file)

            cpu_times[nr][nq] = cpu_time
            io_times[nr][nq] = io_time
            io_sizes[nr][nq] = gets + puts
        if nq not in cpu_times['r']:
            cpu_times['r'][nq] = 0
            io_times['r'][nq] = 0
            io_sizes['r'][nq] = 0

    q_cpu_times = np.sum([list(v.values())
                         for k, v in cpu_times.items() if k != 'r'], axis=0)
    q_io_times = np.sum([list(v.values())
                        for k, v in io_times.items() if k != 'r'], axis=0)
    q_io_sizes = np.sum([list(v.values())
                        for k, v in io_sizes.items() if k != 'r'], axis=0)
    t_cpu_times = np.sum([list(v.values())
                         for v in cpu_times.values()], axis=0)
    t_io_times = np.sum([list(v.values()) for v in io_times.values()], axis=0)
    t_io_sizes = np.sum([list(v.values()) for v in io_sizes.values()], axis=0)
    r_cpu_times = list(cpu_times['r'].values())
    r_io_times = list(io_times['r'].values())
    r_io_sizes = list(io_sizes['r'].values())

    return {
        'query': {'cpu': q_cpu_times, 'io': q_io_times, 'size': q_io_sizes},
        'total': {'cpu': t_cpu_times, 'io': t_io_times, 'size': t_io_sizes},
        'recluster': {'cpu': r_cpu_times, 'io': r_io_times, 'size': r_io_sizes},
        'raw': {'cpu': cpu_times, 'io': io_times, 'size': io_sizes}
    }
