#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

S3_BUCKET = os.environ['S3_BUCKET']
with open('pruned.txt', encoding='utf-8') as f:
    PRUNED = f.read()

data = sys.stdin.read().replace('$PRUNED', PRUNED).replace('$S3_BUCKET', S3_BUCKET)
print(data)
