#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from collections import defaultdict


def wash(file):
    data = defaultdict(dict)

    with open(file, encoding='utf-8') as f:
        lines = f.read().strip().splitlines()

    for line in lines:
        _file, column, size = line.split()
        data[os.path.basename(_file)][column] = int(size)

    return data


base = wash(sys.argv[1])
for file in sys.argv[2:]:
    data = wash(file)
    if data != base:
        print(file)
        for column in data:
            if column not in base:
                print(f'  {column} not in base')
            elif data[column] != base[column]:
                print(f'  {column} {data[column]} != {base[column]}')
        exit(1)

print('identical')
