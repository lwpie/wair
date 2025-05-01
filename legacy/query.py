#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import os
import random
import sys

M = 2

# N = len(os.listdir('tpch')) + 1
N = 26
J = 25

SEGMENTS = ['AUTOMOBILE', 'BUILDING', 'FURNITURE', 'MACHINERY', 'HOUSEHOLD']
NATIONS = ['ALGERIA', 'ARGENTINA', 'BRAZIL', 'CANADA', 'EGYPT', 'ETHIOPIA', 'FRANCE', 'GERMANY', 'INDIA', 'INDONESIA', 'IRAN', 'IRAQ', 'JAPAN',
           'JORDAN', 'KENYA', 'MOROCCO', 'MOZAMBIQUE', 'PERU', 'CHINA', 'ROMANIA', 'SAUDI ARABIA', 'VIETNAM', 'RUSSIA', 'UNITED KINGDOM', 'UNITED STATES']
MODES = ['REG AIR', 'AIR', 'RAIL', 'SHIP', 'TRUCK', 'MAIL', 'FOB']
COLORS = ['almond', 'antique', 'aquamarine', 'azure', 'beige', 'bisque', 'black', 'blanched', 'blue', 'blush', 'brown', 'burlywood', 'burnished', 'chartreuse', 'chiffon', 'chocolate', 'coral', 'cornflower', 'cornsilk', 'cream', 'cyan', 'dark', 'deep', 'dim', 'dodger', 'drab', 'firebrick', 'floral', 'forest', 'frosted', 'gainsboro', 'ghost', 'goldenrod', 'green', 'grey', 'honeydew', 'hot', 'indian', 'ivory', 'khaki', 'lace', 'lavender', 'lawn', 'lemon',
          'light', 'lime', 'linen', 'magenta', 'maroon', 'medium', 'metallic', 'midnight', 'mint', 'misty', 'moccasin', 'navajo', 'navy', 'olive', 'orange', 'orchid', 'pale', 'papaya', 'peach', 'peru', 'pink', 'plum', 'powder', 'puff', 'purple', 'red', 'rose', 'rosy', 'royal', 'saddle', 'salmon', 'sandy', 'seashell', 'sienna', 'sky', 'slate', 'smoke', 'snow', 'spring', 'steel', 'tan', 'thistle', 'tomato', 'turquoise', 'violet', 'wheat', 'white', 'yellow']

random.seed(114514)

q1 = {
    'delta': [random.randint(60, 120) for _ in range(N)]
}

q3 = {
    'segment': random.choices(SEGMENTS, k=N),
    'delta': [random.randint(0, 30) for _ in range(N)]
}

q6 = {
    # 'delta': [random.randint(1, 5) * 12 for _ in range(N)],
    'delta': list(),
    'discount': [random.randint(2, 9) for _ in range(N)],
    'quantity': [random.randint(24, 25) for _ in range(N)]
}

for i in range(N):
    delta = random.randint(1, 5) * 12
    while not delta + 12 < i + J:
        delta = random.randint(1, 5) * 12
    q6['delta'].append(delta)

nation1, nation2 = zip(*[random.sample(NATIONS, k=2) for _ in range(N)])

q7 = {
    'nation1': nation1,
    'nation2': nation2
}

shipmode1, shipmode2 = zip(*[random.sample(MODES, k=2) for _ in range(N)])

q12 = {
    'shipmode1': shipmode1,
    'shipmode2': shipmode2,
    # 'delta': [random.randint(1, 5) * 12 for _ in range(N)]
    'delta': list()
}

for i in range(N):
    delta = random.randint(1, 5) * 12
    while not delta + 12 < i + J:
        delta = random.randint(1, 5) * 12
    q12['delta'].append(delta)

q14 = {
    # 'delta': [random.randint(12, 71) for _ in range(N)]
    'delta': list()
}

for i in range(N):
    delta = random.randint(12, 71)
    while not delta + 1 < i + J:
        delta = random.randint(12, 71)
    q14['delta'].append(delta)

q15 = {
    # 'delta': [random.randint(12, 69) for _ in range(N)]
    'delta': list()
}

for i in range(N):
    delta = random.randint(12, 69)
    while not delta + 3 < i + J:
        delta = random.randint(12, 69)
    q15['delta'].append(delta)

q20 = {
    'color': random.choices(COLORS, k=N),
    # 'delta': [random.randint(1, 5) * 12 for _ in range(N)],
    'delta': list(),
    'nation': random.choices(NATIONS, k=N)
}

for i in range(N):
    delta = random.randint(1, 5) * 12
    while not delta + 12 < i + J:
        delta = random.randint(1, 5) * 12
    q20['delta'].append(delta)

subs = {1: q1, 3: q3, 6: q6, 7: q7, 12: q12, 14: q14, 15: q15, 20: q20}
ys = {k: i for i, k in enumerate(subs.keys())}

x = [0] * len(subs)
xs = [copy.deepcopy(x)]
for i in range(1, N):
    xs.append(copy.deepcopy(xs[i - 1]))
    for j in range(M * (i - 1), M * i):
        xs[i][j % len(xs[i])] += 1


def query(q, n):
    return {k: v[xs[n][ys[q]]] for k, v in subs[q].items()}


if __name__ == '__main__':
    q, n = map(int, sys.argv[1:])
    print('export ', end='')
    for k, v in query(q, n - N).items():
        print(f'{k.upper()}="{v}"', end=' ')
    print()
