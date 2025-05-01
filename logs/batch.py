#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

import numpy as np
from matplotlib import pyplot as plt
from utils import analyze

COLORS = ['#ece7f2', '#a6bddb', '#2b8cbe']

base = 'logs/33/2'
metric = 'cpu'

wair = analyze(os.path.join(base, 'wair'))
dd = analyze(os.path.join(base, 'dd'))
naive = analyze(os.path.join(base, 'naive'))
none = analyze(os.path.join(base, 'none'))


# def split(data):
#     return [sum(data[i:  i + 2]) for i in range(0, len(data), 2)]


wair_query = wair['query'][metric]
dd_query = dd['query'][metric]
naive_query = naive['query'][metric]
none_query = none['query'][metric]

wair_recluster = wair['recluster'][metric]
dd_recluster = dd['recluster'][metric]
naive_recluster = naive['recluster'][metric]
# none_recluster = none['recluster'][metric]

x = np.arange(len(wair_query))
width = 0.35

plt.rcParams.update({'font.size': 16})
fig, ax1 = plt.subplots(figsize=(20, 5))

ax1.bar(x - width / 2, none_query, width, label='No Recluster', zorder=3,
        color=COLORS[0], edgecolor='black')
# ax1.bar(x - width / 2, naive_query, width, label='Query', zorder=3,
#         color=COLORS[1], edgecolor='black')
# ax1.bar(x - width / 2, naive_recluster, width, bottom=naive_query,
#         label='Recluster', zorder=3, color=COLORS[2], edgecolor='black')
# ax1.bar(x + width / 2, dd_query, width, label='Query', zorder=3,
#         color=COLORS[1], edgecolor='black')
# ax1.bar(x + width / 2, dd_recluster, width, bottom=dd_query,
#         label='Recluster', zorder=3, color=COLORS[2], edgecolor='black')
ax1.bar(x + width / 2, wair_query, width, label='Query', zorder=3,
        color=COLORS[1], edgecolor='black')
ax1.bar(x + width / 2, wair_recluster, width, bottom=wair_query,
        label='Recluster', zorder=3, color=COLORS[2], edgecolor='black')
ax1.legend()
ax1.set_xticks(x)
ax1.set_xlim(-1 + width / 2, len(x) - width / 2)

ax1.set_xlabel('Query Batch')
ax1.set_ylabel('Batch Runtime (s)')

ax2 = ax1.twinx()
ax2.plot(np.cumsum(none_query),
         label='No Recluster', zorder=3, color=COLORS[1], linewidth=4)
ax2.plot(np.cumsum(wair_query) + np.cumsum(wair_recluster),
         label='WAIR', zorder=3, color=COLORS[2], linewidth=4)
ax2.set_ylabel('Accumulated Runtime (s)')
# ax2.legend(loc='upper left', bbox_to_anchor=(0.125, 1.0))
ax2.legend(loc='upper left', bbox_to_anchor=(0.135, 1.0))
ax2.grid(axis='y', zorder=-1)

ax1.set_zorder(2)
ax1.set_frame_on(False)

plt.tight_layout()
if len(sys.argv) <= 1:
    plt.show()
else:
    plt.savefig(
        f'{os.path.splitext(os.path.basename(sys.argv[0]))[0]}.pdf', bbox_inches='tight')
