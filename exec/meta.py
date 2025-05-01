#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
from glob import glob

import duckdb
import redis
from parse import compile

from utils import SCHEMA

r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)
s = redis.StrictRedis(host='localhost', port=6379, db=1, decode_responses=True)


def ingest(path):
    with open('file_stats.txt', encoding='utf-8') as f:
        lines = f.read().rstrip().split('\n')

    pipe = r.pipeline()
    for line in lines:
        if line.startswith(' '):
            assert line.endswith('0')
            continue
        file, column, size = line.split(' ')
        pipe.hset(f'{os.path.basename(file)}:{column}',
                  'total_uncompressed_size', size)
    pipe.execute()

    files = glob(os.path.join(path, '*.parquet'))
    files.sort(key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))

    pipe = r.pipeline()
    for file in files:
        data = duckdb.sql(f"SELECT total_uncompressed_size, total_compressed_size, stats_min_value, stats_max_value, path_in_schema FROM parquet_metada\
ta('{file}');").fetchall()
        for row in data:
            total_uncompressed_size, total_compressed_size, stats_min_value, stats_max_value, path_in_schema = row
            entry = f'{os.path.basename(file)}:{path_in_schema}'
            pipe.hset(entry, 'compression_ratio',
                      total_compressed_size / total_uncompressed_size)
            pipe.hset(entry, 'stats_min_value', stats_min_value)
            pipe.hset(entry, 'stats_max_value', stats_max_value)
    pipe.execute()

    pipe = s.pipeline()
    for file in files:
        pipe.sadd('files', os.path.basename(file))
    pipe.execute()


parser = compile('{} AND {:S} IS NOT NULL')


def prune(file='explain.json'):
    with open(file, encoding='utf-8') as f:
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
    filters = [parser.parse(filter).fixed for filter in filters]
    print('\n'.join(predicate for predicate, column in filters), file=sys.stderr)

    files = list(s.smembers('files'))
    files.sort(key=lambda x: int(os.path.splitext(x)[0]))

    pipe = r.pipeline()
    for file in files:
        for _, column in filters:
            pipe.hget(f'{file}:{column}', 'stats_min_value')
            pipe.hget(f'{file}:{column}', 'stats_max_value')
    data = pipe.execute()

    pruned = list()
    for i, file in enumerate(files):
        for j, (predicate, column) in enumerate(filters):
            stats_min_value = data[i * len(filters) * 2 + j * 2]
            stats_max_value = data[i * len(filters) * 2 + j * 2 + 1]
            if SCHEMA[column] == 'DATE':
                stats_min_value = f"'{stats_min_value}'::DATE"
                stats_max_value = f"'{stats_max_value}'::DATE"
            if 'AND' not in predicate:
                results = [duckdb.sql(f"SELECT {predicate.replace(column, stats_min_value)};").fetchone()[0],
                           duckdb.sql(f"SELECT {predicate.replace(column, stats_max_value)};").fetchone()[0]]
                if not any(results):
                    pruned.append(file)
                    break
            else:
                left, right = predicate.split(' AND ')
                results = [duckdb.sql(f"SELECT {left.replace(column, stats_max_value)};").fetchone()[0],
                           duckdb.sql(f"SELECT {right.replace(column, stats_min_value)};").fetchone()[0]]
                if not all(results):
                    pruned.append(file)
                    break

    outcomes = set(files) - set(pruned)
    with open('pruned.txt', 'w', encoding='utf-8') as f:
        f.write(', '.join(f'"$S3_BUCKET/{file}"' for file in outcomes))

    print(len(outcomes), len(files), file=sys.stderr)


if __name__ == '__main__':
    match sys.argv[1]:
        case 'ingest':
            ingest(sys.argv[2])
        case 'prune':
            prune()
        case _:
            assert sys.argv[1]
