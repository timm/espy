#!/usr/bin/env python3
# vim: filetype=python ts=2 sw=2 sts=2 et :

from types import FunctionType as fun
import random
import functools
import math
import sys
import re


class obj:
  def __init__(i, **d): i.__dict__.update(d)
  def __repr__(i): return "{" + ', '.join(
      [f":{k} {v}" for k, v in sorted(i.__dict__.items()) if k[0] != "_"])+"}"


my0 = dict(seed=(10023, "random number seed"),
           k=(1, "low freuecny"),
           m=(2, "low frq"))


class Col(obj):
  @ staticmethod
  def new(tab, at, txt):
    x = (Num if txt[0].isupper() else Sym)(at, txt)
    if "?" not in txt:
      (tab.ys if x.goalp() else tab.xs).append(x)
    return x

  def goalp(i): return "+" == i.txt[-1] or "-" == i.txt[-1]

  def add(i, x):
    if x == "?":
      return x
    i.n += 1
    return i.add1(x)


class Num(Col):
  def __init__(i, at=0, txt=""):
    i.txt, i.at, i.n, i.mu, i.m2, i.sd = txt, at, 0, 0, 0, 0

  def mid(i): return i.mu

  def add1(i, x):
    d = x - i.mu
    i.mu += d/i.n
    i.m2 += d*(x - i.mu)
    i.sd = (i.m2/i.n)**0.5
    return x

  def like(i, x, *_):
    if (i.mu - 3*i.sd) < x < (i.mu + 3*i.sd):
      var = i.sd ** 2
      denom = (math.pi*2*var) ** .5
      num = math.e ** (-(x-i.mu)**2/(2*var+0.0001))
      return num/(denom + 1E-64)
    else:
      return 0


class Sym(Col):
  def __init__(i, at=0, txt=""):
    i.txt, i.at, i.n, i.seen, i.most, i.mode = txt, at, 0, {}, 0, None

  def mid(i): return i.mode

  def like(i, x, prior, my):
    return (i.seen.get(x, 0) + my.m*prior) / (i.n + my.m)

  def add1(i, x):
    tmp = i.seen[x] = i.seen.get(x, 0) + 1
    if tmp > i.most:
      i.most, i.mode = tmp, x
    return x


class Tab(obj):
  def __init__(i):
    i.rows, i.cols, i.xs, i.ys = [], [], [], []

  def x(i): return [col.mid() for col in i.xs]
  def y(i): return [col.mid() for col in i.ys]

  def clone(i, lst=[]):
    t = Tab()
    t.add([col.txt for col in i.cols])
    [t.add(one) for one in lst]
    return t

  def add(i, row):
    if i.cols:
      i.rows += [[col.add(x) for col, x in zip(i.cols, row)]]
    else:
      i.cols = [Col.new(i, at, txt) for at, txt in enumerate(row)]

  def classify(i, row, my, tabs=[]):
    tabs = [i]+tabs
    n = sum(len(t.rows) for t in tabs)
    like = -1E64
    out = tabs[0]
    for t in tabs:
      prior = (len(t.rows) + my.k) / (n + my.k*len(tabs))
      tmp = math.log(prior)
      for col in i.xs:
        v = row[col.at]
        if v != "?":
          if inc := col.like(v, prior, my):
            tmp += math.log(inc)
      if tmp > like:
        like, out = tmp, t
    return like, out


def atom(x):
  try:
    return int(x)
  except Exception:
    try:
      return float(x)
    except Exception:
      return x


def csv(file=None):
  def lines(src):
    for lst in src:
      lst = re.sub(r'([\n\t\r ]|#.*)', '', lst)
      if lst:
        yield [atom(x) for x in lst.split(",")]
  if file:
    with open(file) as fp:
      for lst in lines(fp):
        yield lst
  else:
    for lst in lines(sys.stdin):
      yield lst


#     def gt(a, b): return 0 if id(a) == id(b) else (-1 if i.better(a, b) else 1)
#     return i.rows.sort(key=functools.cmp_to_key(gt))

def eg_one(my):
  "table1"
  def like(r): return t.classify(r, my)[0]
  def r2(x): return round(x, 2)
  t = Tab()
  [t.add(lst) for lst in csv(my.file)]
  t.rows.sort(key=like)
  n = 50
  t1 = t.clone(t.rows[:n])
  t2 = t.clone(t.rows[-n:])

  print("lo  ", [r2(col.mid()) for col in t1.cols])
  print("hi  ", [r2(col.mid()) for col in t2.cols])
  print("mid ", [r2(col.mid()) for col in t.cols])


def main(funs,
         file=sys.argv[2] if "-d" in sys.argv else None,
         my=obj(**{k: v for k, (v, _) in my0.items()})):
  my.file = file
  for k, f in funs.items():
    if type(f) == fun and "eg_" in k:
      print("%", f.__doc__)
      random.seed(my.seed)
      f(my)


main(vars())
#  def better(i, r1, r2):
#     s1, s2, n = 0, 0, len(i.cols.y)
#     for col in i.cols.y:
#       a, b = r1[col.at], r2[col.at]
#       a, b = col.norm(a), col.norm(b)
#       s1 -= math.e**(at.w*(a-b)/n)
#       s2 -= math.e**(at.w*(b-a)/n)
#     return s1/n < s2/n
#
#   def ordered(i, THE):
#
#
