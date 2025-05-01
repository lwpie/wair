#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

import numpy as np
from matplotlib import pyplot as plt
from utils import analyze

# plt.style.use('seaborn-v0_8-whitegrid')
COLORS = ['#f1eef6', '#bdc9e1', '#74a9cf', '#0570b0']
# COLORS = ['#fef0d9', '#fdcc8a', '#fc8d59', '#d7301f']

pools = ['logs/33/2', 'logs/33/6']
metric = 'cpu'

plt.figure(figsize=(20, 5))
plt.rcParams.update({'font.size': 16})

for i, base in enumerate(pools):
    plt.subplot(1, 2, i + 1)
    # plt.ylim(0, 450)
    if i == 0:
        plt.ylabel('Average Runtime (s)')

    wair = analyze(os.path.join(base, 'wair'))['raw'][metric]
    wair = {k: np.average(list(v.values())) for k, v in wair.items()}

    dd = analyze(os.path.join(base, 'dd'))['raw'][metric]
    dd = {k: np.average(list(v.values())) for k, v in dd.items()}

    naive = analyze(os.path.join(base, 'naive'))['raw'][metric]
    naive = {k: np.average(list(v.values())) for k, v in naive.items()}

    none = analyze(os.path.join(base, 'none'))['raw'][metric]
    none = {k: np.average(list(v.values())) for k, v in none.items()}
    none['r'] = 0

    # wair['r'] /= len(wair) - 1
    # none['r'] /= len(none) - 1

    nrs = sorted(wair.keys(), key=lambda x: 114514 if x == 'r' else int(x))
    wair = [wair[k] for k in nrs]
    dd = [dd[k] for k in nrs]
    naive = [naive[k] for k in nrs]
    none = [none[k] for k in nrs]
    print((wair[:-1] / np.array(none[:-1])).tolist())

    x = np.arange(len(nrs))
    width = 0.2

    # plt.bar(x - width/2, none, width, label='No Recluster', zorder=3)
    # plt.bar(x + width/2, wair, width, label='wairamic', zorder=3)
    plt.bar(x - 3 / 2 * width, none, width,
            label='No Recluster', zorder=3, color=COLORS[0], edgecolor='black')
    plt.bar(x - width / 2, naive, width,
            label='Naive', zorder=3, color=COLORS[1], edgecolor='black')
    plt.bar(x + width / 2, dd, width,
            label='DDIR', zorder=3, color=COLORS[2], edgecolor='black')
    plt.bar(x + 3 / 2 * width, wair, width,
            label='WAIR', zorder=3, color=COLORS[3], edgecolor='black')

    nrs[-1] = '*r'
    plt.xticks(x, nrs)
    plt.grid(axis='y', zorder=-1)
    plt.legend()

    plt.xlabel('Query Template')
    match i:
        case 0:
            plt.title('TPC-H W(2)')
        case 1:
            plt.title('TPC-H W(6)')

plt.tight_layout()
if len(sys.argv) <= 1:
    plt.show()
else:
    plt.savefig(
        f'{os.path.splitext(os.path.basename(sys.argv[0]))[0]}.pdf', bbox_inches='tight')
