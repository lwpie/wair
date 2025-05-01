#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from glob import glob
from uuid import uuid4

import duckdb

COL = 'l_shipdate'
PREFIX = 'pool/lineitem'
S3_PREFIX = os.environ['S3_BUCKET']


def ratio(filename):
    return {row[0]: row[1] for row in duckdb.sql(
        f"SELECT path_in_schema, total_compressed_size / total_uncompressed_size FROM parquet_metadata('{os.path.join(PREFIX, filename)}');").fetchall()}


def ratios():
    files = list(map(os.path.basename, glob(
        os.path.join(PREFIX, '*.parquet'))))
    return {filename: ratio(filename) for filename in files}


RATIOS = ratios()


def schema():
    files = glob(os.path.join(PREFIX, '*.parquet'))
    return {row[0]: row[1]
            for row in duckdb.sql(f"DESCRIBE '{files[0]}';").fetchall()}


SCHEMA = schema()


def sizeof(col_name, filename):
    match SCHEMA[col_name]:
        case 'DOUBLE':
            return 8 * RATIOS[filename][col_name]
        case 'BIGINT' | 'UBIGINT':
            return 8 * RATIOS[filename][col_name]
        case 'DECIMAL(15,2)':
            return 8 * RATIOS[filename][col_name]
        case 'DATE':
            return 4 * RATIOS[filename][col_name]
        case 'TIMESTAMP WITH TIME ZONE':
            return 8 * RATIOS[filename][col_name]
        case 'VARCHAR':
            return f'{RATIOS[filename][col_name]} * (bit_length({col_name}) >> 3)'

    assert False


def stats(filename):
    with open(filename, encoding='utf-8') as f:
        data = json.load(f)
    cpu_time = data['cpu_time']

    io_times = list()
    projs = [COL]
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


def recluster(files):
    if files and len(files) > 1:
        files = sorted(files)
        print(len(files))

        # duckdb.sql("SET memory_limit TO '30GB';")
        path = ','.join(
            f"'{os.path.join(PREFIX, filename)}'" for filename in files)
        duckdb.sql(
            f"CREATE TABLE lineitem AS FROM read_parquet([{path}]) ORDER BY {COL};")
        duckdb.sql(
            f"COPY lineitem TO '{(uuid := str(uuid4()))}.parquet';")

        s3_path = ','.join(
            f"'{os.path.join(S3_PREFIX, filename)}'" for filename in files)
        fake_sql = f"COPY (FROM read_parquet([{s3_path}]) ORDER BY {COL}) TO '{os.path.join(S3_PREFIX, 'tmp')}' (FORMAT 'parquet');"
        with open('r.sql', 'w', encoding='utf-8') as f:
            f.write(fake_sql)

        # split(f'{uuid}.parquet')
        os.system(f'./split {uuid}.parquet')
        os.remove(f'{uuid}.parquet')

        replaces = glob(os.path.join(uuid, '*.parquet'))
        replaces.sort(key=lambda x: int(os.path.splitext(
            os.path.basename(x))[0].split('_')[-1]))
        for src, dst in zip(replaces, files):
            os.replace(src, os.path.join(PREFIX, dst))

        if len(replaces) < len(files):
            for filename in files[len(replaces):]:
                os.remove(os.path.join(PREFIX, filename))
        elif len(replaces) > len(files):
            head = min([int(os.path.splitext(os.path.basename(path))[0])
                        for path in glob(os.path.join(PREFIX, '*.parquet'))])
            for filename in replaces[len(files):]:
                head -= 1
                os.rename(filename, os.path.join(PREFIX, f'{head}.parquet'))
                files.append(f'{head}.parquet')

        os.rmdir(uuid)

    else:
        files = replaces = list()

    with open('files.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(files[:len(replaces)]))

    with open('trashes.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(files[len(replaces):]))
