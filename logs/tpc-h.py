#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from glob import glob

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import ticker as tk
from tqdm import tqdm
from utils import analyze, fs, stats

COLORS = ['#f1eef6', '#bdc9e1', '#74a9cf', '#0570b0']
REDS = ['#fef0d9', '#fdcc8a', '#fc8d59', '#d7301f']

base = 'logs/33/2'
metric = 'cpu'


wair = analyze(os.path.join(base, 'wair'))['total'][metric]
dd = analyze(os.path.join(base, 'dd'))['total'][metric]
naive = analyze(os.path.join(base, 'naive'))['total'][metric]
none = analyze(os.path.join(base, 'none'))['total'][metric]

plt.figure(figsize=(20, 5))
plt.rcParams.update({'font.size': 16})

# plt.plot(np.cumsum(none),
#          label='Baseline', color=COLORS[0], linewidth=4)
# plt.plot(np.cumsum(naive),
#          label='Naive', color=COLORS[1], linewidth=4)
# plt.plot(np.cumsum(dd),
#          label='DD', color=COLORS[2], linewidth=4)
# plt.plot(np.cumsum(wair),
#          label='WAIR', color=COLORS[3], linewidth=4)

x = np.arange(len(none))
width = 0.2

plt.bar(x - width / 2 * 3, np.cumsum(none), width,
        label='No Recluster', zorder=3, color=COLORS[0], edgecolor='black')
plt.bar(x - width / 2, np.cumsum(naive), width,
        label='Naive', zorder=3, color=COLORS[1], edgecolor='black')
plt.bar(x + width / 2, np.cumsum(dd), width,
        label='DDIR', zorder=3, color=COLORS[2], edgecolor='black')
plt.bar(x + width / 2 * 3, np.cumsum(wair), width,
        label='WAIR', zorder=3, color=COLORS[3], edgecolor='black')
plt.xticks(x, [str(i) for i in range(1, len(none) + 1)])

plt.xlim(-1 + width / 2, len(x) - width / 2)
plt.grid(axis='y', zorder=-1)
plt.legend()

# plt.yscale('log')
plt.xticks(x, [f'{i}' for i in x])
plt.xlabel('Query Batch')
plt.ylabel('Accumulated Runtime (s)')

# plt.ylim((0, 3e6))

# ratio1 = np.cumsum(wair['total']['cpu'])[30:] / \
#     np.cumsum(none['total']['cpu'])[30:]
# ratio2 = np.cumsum(wair['total']['cpu'])[30:] / \
#     np.cumsum(dd['total']['cpu'])[30:]
# plt.plot(ratio1)
# plt.plot(ratio2)
# plt.show()

# plt.autoscale(enable=True, axis='x', tight=)

plt.tight_layout()
if len(sys.argv) <= 1:
    plt.show()
else:
    plt.savefig(
        f'{os.path.splitext(os.path.basename(sys.argv[0]))[0]}.pdf', bbox_inches='tight')
