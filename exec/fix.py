#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from glob import glob

import redis

BASE = 's'
os.mkdir(BASE)

s = redis.StrictRedis(host='localhost', port=6379, db=1, decode_responses=True)

with open('src.txt', encoding='utf-8') as f:
    files = f.read().strip().splitlines()

replaces = glob('r/*.parquet')
replaces.sort(key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))
for src, dst in zip(replaces, files):
    os.rename(src, os.path.join(BASE, dst))

if len(replaces) < len(files):
    for file in files[len(replaces):]:
        s.srem('files', file)
elif len(replaces) > len(files):
    head = min(int(os.path.splitext(file)[0]) for file in s.smembers('files'))
    for file in replaces[len(files):]:
        head -= 1
        os.rename(file, os.path.join(BASE, f'{head}.parquet'))
        files.append(f'{head}.parquet')

with open('files.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(files[:len(replaces)]))

with open('trashes.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(files[len(replaces):]))
