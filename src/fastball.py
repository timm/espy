#!/usr/bin/env python3
# vim: filetype=python ts=2 sw=2 sts=2 et :
"""
Fast hierarchical active learning v0.2
(c) 2021, Tim Menzies, MIT license

Usage: ./fastball.py -h
       ./fastball.py [OPTIONS]
"""
ABOUT  = dict(
   dir = ("../etc/data/", "where to find data"),
  data = ("auto93.csv",   "data file"),
     k = (1,              "naive bayes low frequency var"),
     m = (2,              "naive bayes low frequency control"),
  seed = (1,              "random number seed"),
 cohen = (.35,            "defines small effects"),
  size = (.5,             "min cluster size control"),
  some = (1024,           "sub-sampling control"))
        
# ----------------------------------------------
import functools, random, copy, math, time, sys, re
from contextlib import contextmanager
from types import FunctionType as fun
from random import random as r

# ----------------------------------------------
def nump(s)  : return s[0].isupper()
def goalp(s) : return "+" in s or "-" in s or "!" in s
def weight(s): return -1 if "<" in s  else 1
def what(s)  : return Skip if "?" in s else (Num if nump(s) else Sym)
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
  def __hash__(i): return id(i)

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

  def div(i, t,my):
    for k in (i.seen | j.seen):  # a 23 b 50
      yield i.seen.get(k, 0), True, (k, k)
      yield j.seen.get(k, 0), False, (k, k)

# ----------------------------------------------
class Num(obj):
  def __init__(i,at=0,txt="",inits=[]): 
    i.txt, i.at, i.w, i.lo, i.hi  = txt, at, weight(txt), math.inf, -math.inf
    i.n, i.mid, i.sd, i.m2 = 0, 0, 0, 0
    i._all = []
    [i.add(x) for x in inits]

  def add(i,x,n=1):
    if x!="?": 
      i.n    += 1
      d       = x - i.mid
      i.mid  += d / i.n
      i.m2   += d * (x - i.mid)
      i.sd    = (i.m2 / i.n)**0.5
      i.lo    = min(x, i.lo)
      i.hi    = max(x, i.hi)
      i._all += [x]

  def div(i, t, my):
    epsilon = i.sd * my.cohen
    width   = len(t.rows)**my.size
    while width < 4 and width < len(t.rows) / 2:
      width *= 1.2
    a = sorted((r for r in t.rows if r[i.at] != "?"), 
                key=lambda r: r[i.at])
    now = obj(at=i.at, x=Num(),  _y=set())
    out = [now]
    for j,row in enumerate(a):
      x = row[i.at]
      if j < len(a) - width:
        if now.x.n >= width:
          if x != a[j+1][i.at]:
            if now.x.hi - now.x.lo > epsilon:
              now  = obj(at=i.at, x=Num(), _y=set())
              out += [now]
      now.x.add(x)
      now._y.add(row)
    out[ 0].lo = -math.inf
    out[-1].hi =  math.inf
    return out

  def merge(i,b4):
    j, tmp, n = 0, [], len(b4)
    while j < n:
      a = b4[j]
      if j < n - 1:
        b = b4[j + 1]
        if c := i.simpler(a,b): a,j = c,j+1
      tmp += [a]
      j += 1
    return i.merge(tmp) if len(tmp) < len(b4) else b4

  def simpler(i,a ,b):
    at      = a.at
    yab     = a._y | b._y
    xab     = Num(inits=[row[at] for row in yab if row[at] != "?"])
    n,n1,n2 = xab.n,  a.x.n,  b.x.n
    s,s1,s2 = xab.sd, a.x.sd, b.x.sd
    if s1+s2 < 0.01 or s*.95 < n1/n*s1 + n2/n*s2:
      return obj(at=a.at, x=xab, y=yab)
 
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
def main(doc,about,funs):
  def option(flag,new):
    assert flag in opt, f"unknown flag -{flag}"
    old = opt[flag]
    new = type(old)(new)
    assert type(new) == type(old), f"-{flag} expects {type(old).__name__}s"
    return new
  
  try:
    opt = {k:v for k,(v,_) in about.items()}
    args= sys.argv
    while args:
      arg, *args = args
      pre,flag = arg[0], arg[1:]
      if  arg=="-h": sys.exit(print(doc+'\nOPTIONS:\n'+ '\n'.join(
                       f" {'-'+k:8} {h:<30} = {v}" 
                       for k,(v,h) in about.items())))
      if pre=="-"  : assert args, f"missing argument for -{flag}"
      if pre=="-"  : opt[flag] = option(flag, args[0])
      if pre=="+"  : opt[flag] = option(flag, True)
      my = obj(**opt)
  except Exception as err: sys.exit(sys.stderr.write("E> "+str(err)+"\n"))
  for s,f in funs.items():
    if type(f)==fun and s[:3] == "eg_":
      start = time.perf_counter(); 
      random.seed(my.seed)
      f(my)
      s = f"{f.__name__:>10}: {time.perf_counter() - start:.4f} secs\n"
      sys.stderr.write(s)
 
# --------------------------------------------------
def eg_show(my): print(my)

def eeg_csv(my): 
  for row in csv(my.dir + my.data): print(row)

def eg_table(my): 
  t= Tab(csv(my.dir + my.data))
  for c in t.xs: 
    if type(c) == Num:
       print("")
       for x in c.div(t,my):
         print("\t",x.x.n)

main(__doc__, ABOUT, locals())

