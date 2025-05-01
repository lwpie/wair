#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import ticker as tk
from glob import glob

from utils import analyze, parse

COLORS = ['#f1eef6', '#bdc9e1', '#74a9cf', '#0570b0']

base = 'logs/20/size'
metric = 'cpu'

s = sorted(os.listdir(base), key=lambda x: int(os.path.basename(x)))

none = np.array([sum(analyze(os.path.join(base, i, 'none'))[
    'total'][metric]) for i in s])
wair = np.array([sum(analyze(os.path.join(base, i, 'wair'))[
    'total'][metric]) for i in s]) / none
naive = np.array([sum(analyze(os.path.join(base, i, 'naive'))[
    'total'][metric]) for i in s]) / none
dd = np.array([sum(analyze(os.path.join(base, i, 'dd'))[
    'total'][metric]) for i in s]) / none
none /= none

plt.figure(figsize=(10, 5))
plt.rcParams.update({'font.size': 16})

x = np.arange(len(s))
width = 0.2

plt.bar(x - width / 2 * 3, none, width,
        label='Baseline', zorder=3, color=COLORS[0], edgecolor='black')
plt.bar(x - width / 2, naive, width,
        label='Naive', zorder=3, color=COLORS[1], edgecolor='black')
plt.bar(x + width / 2, dd, width,
        label='DD', zorder=3, color=COLORS[2], edgecolor='black')
plt.bar(x + width / 2 * 3, wair, width,
        label='WAIR', zorder=3, color=COLORS[3], edgecolor='black')

plt.ylabel('Cost Reduction Ratio')
plt.xlabel('Partition Size (MB)')

plt.grid(axis='y', zorder=0)
plt.xticks(x, s)
plt.gca().yaxis.set_major_formatter(tk.PercentFormatter(1.0))
plt.legend()

plt.tight_layout()
if len(sys.argv) <= 1:
    plt.show()
else:
    plt.savefig(
        f'{os.path.splitext(os.path.basename(sys.argv[0]))[0]}.pdf', bbox_inches='tight')
