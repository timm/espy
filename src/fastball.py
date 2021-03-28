#!/usr/bin/env python3
# vim: filetype=python ts=2 sw=2 sts=2 et :
"""
fastball: hierarchical active learning laboratory.     
(c) 2021 Tim Menzies timm@ieee.org, MIT license.     
"""
import functools, random, math, time, sys, re
from random import random as r
from contextlib import contextmanager
from types import FunctionType as fun

MY = dict(dir  = "../etc/data/",
          data = "auto93.csv",
          k    = 1,
          m    = 2,
          seed = 1,
          some = 1024)

def skip(s)  : return "?" in s
def nump(s)  : return s[0].isupper()
def goalp(s) : return "+" in s or "-" in s or "!" in s
def weight(s): return -1 if "<" in s  else 1
def what(s)  : return Skip if skip(s) else (Num if nump(s) else Sym)

def csv(src=None):
  if src and src[-4:] == ".csv":
    with open(src) as fp:  
      for str in fp: 
       if line := re.sub(r'([\n\t\r ]|#.*)', '', str):
         yield  [x for x in line.split(",")]
  else:
    src = src.split("\n") if src else sys.stdin
    for str in src: 
      if line := re.sub(r'([\n\t\r ]|#.*)', '', str):
        yield  [x for x in line.split(",")]

class obj:
  def __init__(i, **d): i.__dict__.update(d)
  def __repr__(i) : return "{" + ', '.join(
    [f":{k} {v}" for k,v in i.__dict__.items() if k[0] != "_"]) + "}"

class Col(obj):  pass

class Skip(Col):
  def __init__(i, at=0, txt=""): i.txt,i.at = txt,at
  def add(i,x,n=1): return x
  def mid(i): return "?"

class Sym(Col):
  def __init__(i,at=0,txt="",inits=[]): 
    i.txt,i.at,i.n,i.seen,i.most,i.mode = txt,at,0,{},0,None
    [i.add(x) for x in inits]
  def mid(i): return i.mode
  def ent(i): return sum(-v/i.n*math.log(v/i.n) for v in i.seen.values())
  def norm1(i,x)            : return x
  def like(i, x, prior, my) : return (i.seen.get(x,0) + my.m*prior) / (i.n+my.m)
  def add(i,x,n=1):
    if x!="?":
      i.n += n; tmp = i.seen[x] = i.seen.get(x,0) + n
      if tmp>i.most: i.most, i.mode=tmp,x
    return x

  def discretize(i, j, _):
    for k in (i.seen | j.seen):  # a 23 b 50
      yield i.seen.get(k, 0), True, (k, k)
      yield j.seen.get(k, 0), False, (k, k)

  def simplified(i, j):
    k = i.merge(j)
    e1, n1 = i.ent(), i.n
    e2, n2 = j.ent(), j.n
    e, n = k.ent(), k.n
    if e1 + e2 < 0.01 or e * .95 < n1 / n * e1 + n2 / n * e2:
      return k

  def merge(i, j):
    k = Sym(at=i.at, txt=i.txt)
    for seen in [i.seen, j.seen]:
      for x, n in seen.items(): k.add(x, n)
    return k

class Num(Col):
  def __init__(i,at=0,txt="",inits=[]): 
    i.n,i._all,i.ok,i.txt,i.at,i.w=0,[],True,txt,at,weight(txt)
    i.mu =i.m2=i.sd=0
    i.hi = -math.inf
    i.lo =  math.inf
    [i.add(x) for x in inits]
  def mid(i): a=i.all(); return a[len(a)//2]
  def sd(i) : a=i.all(); return (a[9*len(a)//10] - a[len(a)//10])/2.54

  def add(i,x,n=1):
    if x!="?": 
      x=float(x); i.n += 1; i.ok = False; i._all += [x] 
      d = x - i.mu
      i.mu += d / i.n
      i.m2 += d * (x - i.mu)
      i.sd = (i.m2 / i.n)**0.5
      i.lo = min(x, i.lo)
      i.hi = max(x, i.hi)
    return x

  def all(i): 
    if not i.ok: i._all.sort()
    i.ok=True
    return i._all

  def like(i, x, *_):
    if not((i.mu - 4 * i.sd) < x < (i.mu + 4 * i.sd)): return 0
    var = i.sd ** 2
    denom = (math.pi * 2 * var) ** .5
    num = math.e ** (-(x - i.mu)**2 / (2 * var + 0.0001))
    return num / (denom + 1E-64)

  def discretize(i, j, my):
    xy = [(better, True)  for better in i._all] + [
          (bad,    False) for bad    in j._all]
    tmp = div(xy, i.sd() * my.cohen, len(xy)**my.size)
    for bin in merge(tmp):
      for klass, n in bin.also.seen.items():
        yield n, klass, (bin.down, bin.up)

class Tab(obj):
  def __init__(i, rows=[],txt=""):
    i.txt, i.cols,i.xs, i.ys, i.rows = txt,[],[],[],[]
    [i.add(row) for row in rows]

  def clone(i,rows=[],txt=""): 
    return Tab(txt=txt, rows=[[c.txt for c in i.cols]] + rows)

  def y(i): return [col.mid() for col in i.ys]

  def add(i,x):
    if i.cols: 
      i.rows += [[col.add(x0) for col,x0 in zip(i.cols,x)]]
    else: 
      i.cols= [what(s)(j,s) for j,s in enumerate(x)]
      [(i.ys if goalp(col.txt) else i.xs).append(col) for col in i.cols]

  def frequent(i,my):
    return descending([(i.like(r,my),r) for r in i.rows])

  def like(i, row, my): return i.classify(row, my)[0]

  def classify(i, row, my, tabs=[]):
    tabs = [i] + tabs
    n = sum(len(t.rows) for t in tabs)
    mostlike,out = -math.inf,None
    for t in tabs:
      out = out or t
      prior = (len(t.rows) + my.k) / (n + my.k * len(tabs))
      tmp = math.log(prior)
      for col in t.xs:
        v = row[col.at]
        if v != "?":
          if inc := col.like(v, prior, my): tmp += math.log(inc)
      if tmp > mostlike:
        mostlike, out = tmp, t
    return math.e**mostlike, out

def descending(lst):
  return sorted(lst, key=functools.cmp_to_key(
         lambda a,b: 0 if a[0]==b[0] else (1 if a[0]<b[0] else -1)))

def fastball(tab,my): return fastball1(tab,my, len(tab.rows)**.5,0)

def fastball1(tab,my,stop,lvl):
  print(lvl,len(tab.rows), ', '.join([str(x) for x in tab.y()]))
  if len(tab.rows) > 1024:
     tab = tab.clone(random.sample(tab.rows, 1024))
  if len(tab.rows) > stop:
    a= tab.frequent(my)
    t1,t2= tab.clone(), tab.clone()
    m = 1*len(tab.rows)//3
    fastball1(tab.clone([x[1] for x in a[:m]]),my,stop,lvl+1)
    fastball1(tab.clone([x[1] for x in a[m:]]),my,stop,lvl+1)

# --------------------------------------------------
@contextmanager
def watch(txt):
  start = time.perf_counter(); 
  yield; 
  print(f"{txt:>10}: {time.perf_counter() - start:.4f}")

def cli(opt,args):
  def cli1(flag,new):
    assert flag in opt,"undefined flag"
    old = opt[flag]
    new = type(old)(new)
    assert type(new) == type(old), "bad type"
    return new
  #---------------------
  while args:
    arg, *args = args
    pre,flag = arg[0], arg[1:]
    if pre=="+": opt[flag] = cli1(flag, True)
    if pre=="-": 
      assert args, f"missing argument for -{flag}"
      opt[flag] = cli1(flag, args[0])
  return opt

def main(d):
  def do(f,my): 
    with watch(f.__name__): random.seed(my.seed);f(my)
  my= obj(**cli(MY,sys.argv))
  [do(f,my) for s,f in d.items() if type(f)==fun and s[:3] == "eg_"] 

# --------------------------------------------------
def eg_show(my): 
  print(my)
def eeg_csv(my): 
  for row in csv(my.dir + my.data): 1 #print(row)

def eeg_table(my): 
  t= Tab(csv(my.dir + my.data))
  fastball(t, my)

main(locals())
