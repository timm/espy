#!/usr/bin/env python3
# vim: filetype=python ts=2 sw=2 sts=2 et :
"""
es.py /əˈspī/ verb LITERARY see something that is hidden, or obscure.
Optimizer, written as a data miner.

Break the data up into regions of 'bad' and 'better'. 'Interesting'
things occur at very different frequencies in 'bad' and 'better'.
Find interesting bits. Combine them. Repeat. Nearly all this
processing takes log linear time.

     :-------:                 explore  = better==bad
     | Ba    | Bad <----.      planning = max(better - bad)
     |    56 |          |      monitor  = max(bad - better)
     :-------:------:   |      tabu     = min(bad + better)
             | B    |   v
             |    5 | Better
             :------:
"""
import itertools
import math
import sys
import re
from etc import obj, csv, subsets

HELP = dict(
    k=(1, "k Bayes low frequency control"),
    m=(2, "m Bayes low frequency control"),
    best=(.2, "desired size of best set"),
    top=(10, "how many max to try"),
    min=(20, "if rows less than 'min, then 'best'=.5"),
    size=(.5, "min size of breaks"),
    cohen=(.2, "var min"),
    dir=("opt/data/", "dir to data"),
    data=("auto93.csv", "data file"),
    seed=(1, "random number seed"))

LO = -math.inf
HI = math.inf
TINY = 1E-32
NO = "?"


class Bin(obj):
  def __init__(i, down=LO, up=HI): i.down, i.up, i.also = down, up, Sym()


class Tab(obj):
  def __init__(i, src):
    i.rows, i.cols, i.xs, i.ys = [], [], [], []
    for row in src:
      row = row.cells if type(row) == Row else row
      if i.cols:
        i.rows += [Row([col.add(x) for col, x in zip(i.cols, row)], i)]
      else:
        i.cols = [(Num(pos, txt) if txt[0].isupper() else Sym(pos, txt))
                  for pos, txt in enumerate(row)]
        i.ys = [col for col in i.cols if col.goalp]
        i.xs = [col for col in i.cols if not col.goalp]
    i.rows = sorted(i.rows, reverse=True)

  def clone(i, inits=[]): return Tab([[col.txt for col in i.cols]] + inits)
  def goals(i): return [col.mid() for col in i.ys]


class Row(obj):
  def __init__(i, cells, tab): i.cells, i.tab = cells, tab

  def __lt__(i, j):
    s1, s2, n = 0, 0, len(i.tab.ys)
    for col in i.tab.ys:
      pos, w = col.pos, col.w
      a, b = i.cells[pos], j.cells[pos]
      a, b = col.norm(a), col.norm(b)
      s1 -= math.e**(w * (a - b) / n)
      s2 -= math.e**(w * (b - a) / n)
    return s1 / n < s2 / n


class Sym(obj):
  def __init__(i, pos=0, txt=""):
    i.pos, i.txt, i.n, i.goalp = pos, txt, 0, False
    i.seen, i.mode, i.most = {}, None, 0

  def add(i, x, n=1):
    if x != NO:
      i.n += n
      tmp = i.seen[x] = n + i.seen.get(x, 0)
      if tmp > i.most:
        i.most, i.mode = tmp, x
    return x

  def ent(i): return sum(-v / i.n * math.log(v / i.n) for v in i.seen.values())

  def simplified(i, j):
    k = i.merge(j)
    e1, n1 = i.ent(), i.n
    e2, n2 = j.ent(), j.n
    e, n = k.ent(), k.n
    if e1 + e2 < 0.01 or e * .95 < n1 / n * e1 + n2 / n * e2:
      return k

  def merge(i, j):
    k = Sym(pos=i.pos, txt=i.txt)
    for seen in [i.seen, j.seen]:
      for x, n in seen.items():
        k.add(x, n)
    return k

  def discretize(i, j, _):
    for k in (i.seen | j.seen):  # a 23 b 50
      yield i.seen.get(k, 0), True, (k, k)
      yield j.seen.get(k, 0), False, (k, k)


class Num(obj):
  def __init__(i, pos=0, txt=""):
    i.pos, i.txt, i.n = pos, txt, 0
    i.w = -1 if "-" == txt[-1] else 1
    i.goalp = "+" == txt[-1] or "-" == txt[-1]
    i._all, i.ok = [], False

  def discretize(i, j, MY):
    xy = [(better, True) for better in i._all] + [
        (bad, False) for bad in j._all]
    tmp = div(xy, tooSmall=i.sd() * MY.cohen, width=len(xy)**MY.size)
    for bin in merge(tmp):
      for klass, n in bin.also.seen.items():
        yield n, klass, (bin.down, bin.up)

  def add(i, x, **_):
    if x == NO:
      return x
    i.n += 1
    x = float(x)
    i._all += [x]
    i.ok = False
    return x

  def _alls(i):
    i._all = i._all if i.ok else sorted(i._all)
    i.ok = True
    return i._all

  def sd(i): return (i._per(.9) - i._per(.1)) / 2.56
  def mid(i): return i._per(.5) if i._all else None
  def _per(i, p): a = i._alls(); return a[int(p * len(a))]
  def norm(i, x): a = i._alls(); return (x - a[0]) / (a[-1] - a[0] + TINY)


def div(xy, tooSmall=0.01, width=20):
  while width < 4 and width < len(xy) / 2:
    width *= 1.2
  xy = sorted(xy)
  now = Bin(down=xy[0][0], up=xy[0][0])
  out = [now]
  for j, (x, y) in enumerate(xy):
    if j < len(xy) - width:
      if now.also.n >= width:
        if x != xy[j + 1][0]:
          if now.up - now.down > tooSmall:
            now = Bin(down=now.up, up=x)
            out += [now]
    now.up = x
    now.also.add(y)
  out[0].down = LO
  out[-1].up = HI
  return out


def merge(b4):
  j, tmp, n = 0, [], len(b4)
  while j < n:
    a = b4[j]
    if j < n - 1:
      b = b4[j + 1]
      if c := a.also.simplified(b.also):
        a = Bin(a.down, b.up)
        a.also = c
        j += 1
    tmp += [a]
    j += 1
  return merge(tmp) if len(tmp) < len(b4) else b4


def betterBad(tab, MY):
  border = len(tab.rows) * MY.best
  if border < MY.min:
    border = .5 * len(t.rows)
  border = int(border)
  return tab.clone(tab.rows[:int(border)]), tab.clone(tab.rows[int(border):])


def contrast(here, there, MY):
  def seen():
    return {(kl, (col1.txt, col1.pos, span)): f
            for col1, col2 in zip(here.xs, there.xs)
            for f, kl, span in col1.discretize(col2, MY)}

  def like(rule, kl):
    prior = (hs[kl] + MY.k) / (n + MY.k * 2)
    fs = {}
    for txt, pos, span in rule:
      fs[txt] = fs.get(txt, 0) + f.get((kl, (txt, pos, span)), 0)
    parts = [prior, *[(f + MY.m*prior) / (hs[kl] + MY.m) for f in fs.values()]]
    like = math.e**sum(map(math.log, parts))
    return like

  def value(rule):
    b = like(rule, True)
    r = like(rule, False)
    return b**2 / (b + r) if (b+r) > 0.01 and b > r else 0

  def solos(lst):
    for kl, x in f:
      if kl == True:
        if s := value([x]):  # if zero, then skip x
          lst += [(s, x)]
    return lst

  def top(lst): return [x for _, x in sorted(lst, reverse=True)[:MY.top]]

  f = seen()
  n = len(here.rows) + len(there.rows)
  hs = {True: len(here.rows), False: len(there.rows)}
  return top([(value(rule), rule) for rule in subsets(top(solos([])))])


def canonical(rule):
  def merge(b4):
    if len(b4) == 1 and b4 == [(LO, HI)]:
      return None
    j, tmp = 0, []
    while j < len(b4):
      a = b4[j]
      if j < len(b4)-1:
        b = b4[j+1]
        if a[1] == b[0]:
          a = (a[0], b[1])
          j += 1
      tmp += [a]
      j += 1
    return tmp if len(tmp) == len(b4) else merge(tmp)
  cols = {}
  for col, _, span in rule:
    cols[col] = cols.get(col, []) + [span]
  out = {}
  for k, v in cols.items():
    if v1 := merge(sorted(v)):
      out[k] = v1
  return out


def showRulest(tab, rules):

  def selects(tab, rule):
    def selectors(val, ors):
      for (lo, hi) in ors:
        if lo <= val < hi:
          return True
      return False

    def selects1(row, ands):
      for (txt, ors) in ands:
        val = row[tab.cols.named[txt].pos]
        if val != NO:
          if not selectors(val, ors):
            return False
      return True
    s, rule = rule
    return tab.clone([row for row in tab.rows if selects1(row, rule)])

  def showRule(r):
    def showRange(x): return Bin(x[0], x[1]).show()

    def show1(k, v):
      return k + " " + ' or '.join(map(showRange, v))
    s, rule = r
    out = ""
    return ' and '.join([show1(k, v) for k, v in rule])
