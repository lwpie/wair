#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import ticker as tk

from utils import analyze, parse

COLORS0 = ['#ece7f2', '#a6bddb', '#2b8cbe']
COLORS1 = ['#f1eef6', '#bdc9e1', '#74a9cf', '#0570b0']

base = 'logs/33/2'
metric = 'cpu'

wair = analyze(os.path.join(base, 'wair'))
f10 = analyze(os.path.join(base, '20'))
f100 = analyze(os.path.join(base, '200'))
none = analyze(os.path.join(base, 'none'))

none_total = sum(none['total'][metric])

wair_query = sum(wair['query'][metric])
f10_query = sum(f10['query'][metric])
f100_query = sum(f100['query'][metric])

wair_recluster = sum(wair['recluster'][metric])
f10_recluster = sum(f10['recluster'][metric])
f100_recluster = sum(f100['recluster'][metric])

labels = ['Fix(20)', 'Dynamic', 'Fix(200)']
query_cost = np.array([f10_query, wair_query, f100_query]) / none_total
recluster_cost = np.array(
    [f10_recluster, wair_recluster, f100_recluster]) / none_total

plt.rcParams.update({'font.size': 18})
fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(16, 7), width_ratios=[1, 3])

ax0.bar(labels, recluster_cost, label='Recluster', zorder=3, color=COLORS0[-1])
ax0.bar(labels, query_cost, bottom=recluster_cost, label='Query', zorder=3,
        color=COLORS0[-2])

ax0.grid(axis='y', zorder=-1)
ax0.legend()

ax0.yaxis.set_major_formatter(tk.PercentFormatter(1.0))
ax0.set_ylabel('Runtime (% of Baseline)')
ax0.set_title('Overall Performance')

wair = parse(os.path.join(base, 'wair'))
f10 = [20] * len(wair)
f100 = [200] * len(wair)

x = np.arange(1 / len(wair), 1 + 1 / len(wair), 1 / len(wair))

# plt.figure(figsize=(10, 6))
ax1.plot(x, np.cumsum(f10), '.-', linewidth=4,
         markersize=12, label='WAIR', color=COLORS1[1])
ax1.plot(x, np.cumsum(f100), '.-', linewidth=4,
         markersize=12, label='Fix(200)', color=COLORS1[2])
ax1.plot(x, np.cumsum(wair), '.-', linewidth=4,
         markersize=12, label='Fix(20)', color=COLORS1[3])

ax1.set_axisbelow(True)
ax1.grid(axis='y', zorder=-1)
ax1.legend()

ax1.xaxis.set_major_formatter(tk.PercentFormatter(1.0))
ax1.set_xlabel('Ingested Partitions (% of Pool Size)')
ax1.set_ylabel('Accumulated #partitions reclustered')
ax1.set_title('Recluster Aggressiveness')
# ax1.tight_layout()

# fig.suptitle('Recluster Strategy')

plt.tight_layout()
if len(sys.argv) <= 1:
    plt.show()
else:
    plt.savefig(
        f'{os.path.splitext(os.path.basename(sys.argv[0]))[0]}.pdf', bbox_inches='tight')
