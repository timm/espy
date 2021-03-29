#!/usr/bin/env python3
# vim: filetype=python ts=2 sw=2 sts=2 et :
THIS=dict(
  about     = dict(what="fast hierarchical active learning",
                   author    = "Tim Menzies",
                   copyright = "(c) 2021, MIT license",
                   version   = 0.2),
  dir       = "../etc/data/",
  data      = "auto93.csv",
  k         = 1,
  m         = 2,
  seed      = 1,
  cohen     = .35,
  size      = .5,
  some      = 1024)

# ----------------------------------------------
import functools, random, math, time, sys, re
from random import random as r
from contextlib import contextmanager
from types import FunctionType as fun

# ----------------------------------------------
def skip(s)  : return "?" in s
def nump(s)  : return s[0].isupper()
def goalp(s) : return "+" in s or "-" in s or "!" in s
def weight(s): return -1 if "<" in s  else 1
def what(s)  : return Skip if skip(s) else (Num if nump(s) else Sym)
def same(s)  : return s

def csv(src=None):
  def cells(s, fs):
    if s := re.sub(r'([\n\t\r ]|#.*)', '', s):
      lst = s.split(',')
      if fs:
        lst = [(x if x=="?" else f(x)) for f,x in zip(fs,s.split(','))]
      else:
        for x in lst: fs += [float if nump(x) else same]
      return lst 
  fs=[]
  if src and src[-4:] == ".csv":
    with open(src) as fp:  
      for str in fp: 
        if row := cells(str,fs): yield row
  else:
    src = src.split("\n") if src else sys.stdin
    for str in src: 
      if row := cells(str,fs): yield row

class obj:
  def __init__(i, **d): i.__dict__.update(d)
  def __repr__(i) : return "{" + ', '.join(
    [f":{k} {v}" for k,v in i.__dict__.items() if k[0] != "_"]) + "}"

# ----------------------------------------------
class Skip(obj):
  def __init__(i, at=0, txt=""): i.txt,i.at = txt,at
  def add(i,x,n=1): return x
  def mid(i): return "?"

# ----------------------------------------------
class Sym(obj):
  def __init__(i,at=0,txt="",inits=[]): 
    i.txt,i.at,i.n,i.seen,i.most,i.mid = txt,at,0,{},0,None
    [i.add(x) for x in inits]

  def ent(i): return sum(-v/i.n*math.log(v/i.n) for v in i.seen.values())

  def add(i,x,n=1):
    if x!="?":
      i.n += n
      tmp = i.seen[x] = i.seen.get(x,0) + n
      if tmp>i.most: i.most, i.mid = tmp,x

  def bins(i, t,my):
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

# ----------------------------------------------
class Num(obj):
  def __init__(i,at=0,txt="",inits=[]): 
    i.txt, i.at, i.w, i.lo, i.hi  = txt, at, weight(txt), math.inf, -math.inf
    i.n, i.mid, i.sd, i.m2 = 0, 0, 0, 0
    [i.add(x) for x in inits]

  def add(i,x,n=1):
    if x!="?": 
      i.n   += 1
      d      = x - i.mid
      i.mid += d / i.n
      i.m2  += d * (x - i.mid)
      i.sd   = (i.m2 / i.n)**0.5
      i.lo   = min(x, i.lo)
      i.hi   = max(x, i.hi)
  
  def bins(i, t, my):
    epsilon = i.sd * my.cohen
    width   = len(t.rows)**my.size
    while width < 4 and width < len(t.rows) / 2:
      width *= 1.2
    a = sorted((r for r in t.rows if r[i.at] != "?"), key=lambda r: r[i.at])
    x = a[0][i.at]
    n=0
    now = obj(at=i.at, n=n, lo=x, hi=x,  _seen=set())
    out = [now]
    for j,row in enumerate(a):
      x = row[i.at]
      if j < len(a) - width:
        if len(now._seen) >= width:
          if x != a[j+1][i.at]:
            if now.hi - now.lo > epsilon:
              n +=1
              now  = obj(at=i.at, n=n,lo=now.hi, hi=x,  _seen=set())
              out += [now]
      now.hi = x
      now._seen.add(row)
    out[ 0].lo = -math.inf
    out[-1].hi =  math.inf
    return out

# -----------------------------------------------
class Row(obj):
  def __init__(i,cells)   : i.cells=cells
  def __getitem__(i,k)    : return  i.cells[k]
  def __setitem__(i,k,v)  : i.cells[k]=v
  def __iter__(i)         : return iter(i.cells)
  def __len__(i)          : return len(i.cells)

# ----------------------------------------------
class Tab(obj):
  def __init__(i, rows=[],txt=""):
    i.txt, i.cols,i.xs, i.ys, i.rows = txt,[],[],[],[]
    [i.add(row) for row in rows]

  def clone(i,rows=[],txt=""): 
    return Tab(txt=txt, rows=[[c.txt for c in i.cols]] + rows)

  def y(i): return [col.mid() for col in i.ys]

  def add(i,row):
    row = row.cells if type(row)==Row else row
    if i.cols: 
      [col.add(x) for col,x in zip(i.cols,row)]
      i.rows += [Row(row)]
    else: 
      i.cols= [what(s)(j,s) for j,s in enumerate(row)]
      [(i.ys if goalp(col.txt) else i.xs).append(col) for col in i.cols]

# ----------------------------------------------
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
  # --------------------
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
  my= obj(**cli(THIS, sys.argv))
  [do(f,my) for s,f in d.items() if type(f)==fun and s[:3] == "eg_"] 

# --------------------------------------------------
def eeg_show(my): print(my)

def eeg_csv(my): 
  for row in csv(my.dir + my.data): print(row)
  #print(row)

def eg_table(my): 
  t= Tab(csv(my.dir + my.data))
  #for r in t.rows: print(r)
  for c in t.xs: print(c.bins(t,my))

main(locals())
