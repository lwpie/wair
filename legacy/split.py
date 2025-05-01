#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import os
import sys

import pyarrow.parquet as pq
from tqdm import tqdm


def split(filename, target=32 * 1024 * 1024, threshold=0.01):
    def estimate(chunk):
        assert chunk.num_rows > 0
        sink = io.BytesIO()
        pq.write_table(chunk, sink, row_group_size=chunk.num_rows)
        return sink.getbuffer().nbytes

    base = os.path.splitext(filename)[0]
    os.mkdir(base)

    table = pq.read_table(filename)

    i = 0
    head = 0
    step = 122880 * 10

    bar = tqdm(total=table.num_rows)
    while True:
        right = step
        while estimate(chunk := table.slice(head, right)) < target:
            if head + right >= table.num_rows:
                pq.write_table(chunk, os.path.join(
                    base, f'{i}.parquet'), row_group_size=chunk.num_rows)
                bar.update(table.num_rows - head)
                return i + 1
            right += step
        left = right - step
        right = min(right, table.num_rows - head)

        while left < right:
            width = (left + right) // 2
            size = estimate(chunk := table.slice(head, width))
            err = (size - target) / target
            # print(err)

            if abs(err) < threshold:
                pq.write_table(chunk, os.path.join(
                    base, f'{i}.parquet'), row_group_size=chunk.num_rows)
                break

            elif err > 0:
                right = width
            else:
                left = width

        i += 1
        head += width
        bar.update(width)

        if head == table.num_rows:
            return i
        assert head < table.num_rows


if __name__ == '__main__':
    split(sys.argv[1])
