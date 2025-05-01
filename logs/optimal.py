#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import ticker as tk

from utils import analyze

COLORS = ['#f1eef6', '#bdc9e1', '#74a9cf', '#0570b0']

base = 'logs/33'
metric = 'cpu'

wair = np.cumsum(analyze(os.path.join(base, '2/wair'))['total'][metric])
optimal = np.cumsum(analyze(os.path.join(base, 'optimal'))['total'][metric])

plt.rcParams.update({'font.size': 16})
# plt.figure(figsize=(10, 5))
fig, ax1 = plt.subplots(figsize=(12, 5))

ax1.plot(wair, label='WAIR', zorder=3, color=COLORS[-1], linewidth=4)
ax1.plot(optimal, label='Optimal', zorder=3, color=COLORS[-2], linewidth=4)

ax1.set_ylabel('Accumulated Runtime (s)')
ax1.set_xticks(range(0, len(wair), 2))
ax1.grid(axis='y', zorder=-1)
ax1.legend()

ax2 = ax1.twinx()
ax2.plot(wair / optimal - 1, color=COLORS[1],
         marker='o', markersize=12, label='Speedup', linewidth=4)
print(wair / optimal - 1)

# ax2.set_ylim(0.1, 0.3)
# ax2.set_yticks(np.arange(0.1, 0.35, 0.05))
ax2.yaxis.set_major_formatter(tk.PercentFormatter(1.0, decimals=0))
ax2.set_ylabel('Gap to Optimal')

ax1.set_zorder(2)
ax1.set_frame_on(False)
ax1.set_xlabel('Query Batch')

plt.tight_layout()
if len(sys.argv) <= 1:
    plt.show()
else:
    plt.savefig(
        f'{os.path.splitext(os.path.basename(sys.argv[0]))[0]}.pdf', bbox_inches='tight')
