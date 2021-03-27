#!/usr/bin/env python3
# vim: filetype=python ts=2 sw=2 sts=2 et :
"""
fastball: hierrhical active learning laboratory.     
(c) 2021 Tim Menzies timm@ieee.org, MIT license.     
"""
from contextlib import contextmanager
import time
import random,re
from random import random as r
from types import FunctionType as fun

MY = dict(some=1023)

def nump(s): return s[0].isupper()
def goalp(s): return "+" in s or "-" in s or "!" in s
def weight(s): return -1 if "<" in s  else 1
def one(lst,n=1): return lst[int(n*random.randrange(len(lst)))]

def csv(src=None):
  def cells(line):
    if line := re.sub(r'([\n\t\r ]|#.*)', '', line):
      line= [x for x in line.split(",")]
  #------------------------------
  if src and src[-4:] == ".csv":
    with open(src) as fp:  
      for str in fp: 
        if lst := cells(str): yield lst
  else:
    src = src.split("\n") if src else sys.stdin
    for str in src: 
      if lst := cells(str): yield lst

class obj:
  def __init__(i, **d): i.__dict__.update(d)
  def __repr__(i) : return "{" + ', '.join(
      [f":{k} {v}" for k, v in sorted(i.__dict__.items()) if k[0] != "_"]) + "}"

class Col(obj):
  def add(i,x,my,n=1): 
    if x!="?": i.n+=n; return i.add1(x,my,n)
    return x

class Sym(Col):
  def __init__(i,at,s): i.txt,i.at,i.seen,i.most,i.mode = s,at,{},0,None
  def add1(i,x,my,n):
    tmp=i.seen[x]=i.seen.get(x) + n
    if tmp>i.most: i.most, i.mode=tmp,x
    return x

class Some(Col):
  def __init__(i,at,s): i.txt,i.at,i.all,i.w=s,at,[],weight(s)
  def add1(i,x,my,_):
    x=float(x)
    if len(i.all) < my.some.max: i.all += [x]
    elif r() < i.n/my.some.max:  i.all[int(r()*len(i.all))] = x
    return x  

class Table(obj):
  def __init__(i, my,rows=[]):
   i.cols,i.x, i.y, i.rows = [],[],[],[]
   [i.add(row,my) for row in rows]

  def add(i,x,my):
    if    i.cols: i.rows+= [[col.add(x,my) for col in i.cols]]
    else: 
          i.cols= [(Num(j,s) if nump(s) else Sym(j,s)) for j,s in enumerate(row)]
          for col in i.cols:
            (i.y if goalp(col.txt) else i.x).append(col)

@contextmanager
def watch():
  start = time.perf_counter(); yield; print(time.perf_counter() - start)

def eg_table(my): Table(my,csv("../etc/data/auto93.csv"))

def main(d):
  for s,f in d.items():
    if type(f)==fun and s[:3] == "eg_": f(obj(**MY))

#main(locals())

for row in csv("../etc/data/auto93.csv"): print(row)
